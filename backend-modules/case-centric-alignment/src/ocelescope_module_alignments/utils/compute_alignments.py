import traceback

import r4pm
from ocelescope import OCEL, PetriNet
from ocelescope_module_alignments.models.alignment import (
    Aggregated,
    AlignmentsResponse,
    FitnessResult,
    NetArc,
    NetPlace,
    NetTransition,
    ResponseNet,
    TransitionStat,
    VariantAlignmentResult,
)
from r4pm.bindings._types import AcceptingPetriNet as R4PMPetriNet
from r4pm.bindings._types import AlignmentOptions, AlphaPPPConfig
from r4pm.bindings._types import VariantAlignmentResult as R4PMVariantAlignmentResult


class AlignmentComputationError(Exception):
    def __init__(self, message: str, trace: str | None = None):
        super().__init__(message)
        self.trace = trace or message


def to_r4pm_format(petri_net: PetriNet) -> R4PMPetriNet:
    place_index = {p.name: i for i, p in enumerate(petri_net.places)}
    transition_index = {t.name: i for i, t in enumerate(petri_net.transitions)}

    inputs: dict[int, list[tuple[int, int]]] = {i: [] for i in transition_index.values()}
    outputs: dict[int, list[tuple[int, int]]] = {i: [] for i in transition_index.values()}
    for arc in petri_net.arcs:
        if arc.source in place_index:
            inputs[transition_index[arc.target]].append((place_index[arc.source], arc.weight))
        else:
            outputs[transition_index[arc.source]].append((place_index[arc.target], arc.weight))

    return {
        "places": [{"name": p.name} for p in petri_net.places],
        "transitions": [
            {"name": t.name, "label": t.label, "inputs": inputs[i], "outputs": outputs[i]}
            for t, i in ((t, transition_index[t.name]) for t in petri_net.transitions)
        ],
        "initial_marking": {str(place_index[name]): count for name, count in petri_net.initial_marking.items()},
        "final_marking": {str(place_index[name]): count for name, count in petri_net.final_marking.items()},
    }


def flatten(petri_net: PetriNet, object_type: str) -> PetriNet:
    place_names = {p.name for p in petri_net.places if p.object_type == object_type}
    places_flatten = [p for p in petri_net.places if p.name in place_names]

    arcs_flatten = []
    connected_transition_names = set()
    for arc in petri_net.arcs:
        source_is_place = arc.source in place_names
        target_is_place = arc.target in place_names
        if not (source_is_place or target_is_place):
            continue
        arcs_flatten.append(arc)
        if not source_is_place:
            connected_transition_names.add(arc.source)
        if not target_is_place:
            connected_transition_names.add(arc.target)

    transitions_flatten = [t for t in petri_net.transitions if t.name in connected_transition_names]

    initial_marking_flatten = {name: count for name, count in petri_net.initial_marking.items() if name in place_names}
    final_marking_flatten = {name: count for name, count in petri_net.final_marking.items() if name in place_names}

    return PetriNet(
        places=places_flatten,
        transitions=transitions_flatten,
        arcs=arcs_flatten,
        initial_marking=initial_marking_flatten,
        final_marking=final_marking_flatten,
    )


def place_id(index: int | str) -> str:
    return f"p{index}"


def transition_id(index: int | str) -> str:
    return f"t{index}"


def convert_net(petri_net: R4PMPetriNet) -> ResponseNet:
    places = [NetPlace(id=place_id(i)) for i in range(len(petri_net["places"]))]
    transitions = [
        NetTransition(id=transition_id(i), label=t.get("label")) for i, t in enumerate(petri_net["transitions"])
    ]
    arcs = [
        *(
            NetArc(nodes=(place_id(p), transition_id(i)), weight=w)
            for i, t in enumerate(petri_net["transitions"])
            for p, w in t["inputs"]
        ),
        *(
            NetArc(nodes=(transition_id(i), place_id(p)), weight=w)
            for i, t in enumerate(petri_net["transitions"])
            for p, w in t["outputs"]
        ),
    ]

    return ResponseNet(
        places=places,
        transitions=transitions,
        arcs=arcs,
        initial_marking={place_id(k): v for k, v in (petri_net.get("initial_marking") or {}).items()},
        final_marking={place_id(k): v for k, v in (petri_net.get("final_marking") or {}).items()},
    )


def is_flattened(petri_net: PetriNet) -> bool:
    object_types = set()
    for place in petri_net.places:
        object_types.add(place.object_type)
        if len(object_types) > 1:
            return False

    return len(object_types) == 1


def preprocessing(
    ocel: OCEL, object_type: str, petri_net: PetriNet | None
) -> tuple[r4pm.handles.EventLogActivityProjection, R4PMPetriNet]:
    config: AlphaPPPConfig = {
        "absolute_df_clean_thresh": 1,
        "balance_thresh": 0.2,
        "fitness_thresh": 0.2,
        "log_repair_loop_df_thresh_rel": 0.2,
        "log_repair_skip_df_thresh_rel": 0.2,
        "relative_df_clean_thresh": 0.2,
        "replay_thresh": 0.2,
    }
    event_log_df = ocel.sql(f"""
        SELECT
            rel."ocel:oid" as "case:concept:name",
            ev."ocel:timestamp" as "time:timestamp",
            ev."ocel:activity" as "concept:name"
        FROM
            e2o rel
            RIGHT JOIN (
                SELECT
                    *
                FROM
                    objects
                WHERE
                    "ocel:type" = '{object_type}'
                ) ob USING ("ocel:oid")
            LEFT JOIN (
            SELECT
            *
            FROM
            events
            ) ev USING ("ocel:eid")
            ORDER BY
            ("time:timestamp", "case:concept:name", "concept:name")
                """).pl()

    log_id = r4pm.import_item_from_df("EventLog", event_log_df)
    proj_id = r4pm.convert_item(str(log_id), "EventLogActivityProjection")
    assert isinstance(proj_id, r4pm.handles.EventLogActivityProjection)
    if petri_net:
        if is_flattened(petri_net):
            process_model = to_r4pm_format(petri_net)
        else:
            process_model = to_r4pm_format(flatten(petri_net, object_type))
    else:
        process_model = r4pm.bindings.discover_alphappp_net(proj_id, options=config)
    return proj_id, process_model


def variant_alignment(
    proj_id: r4pm.handles.EventLogActivityProjection,
    process_model: R4PMPetriNet,
    options: AlignmentOptions | None = None,
) -> list[R4PMVariantAlignmentResult]:
    return r4pm.bindings.align_variants(process_model, proj_id, options)


def compute_fitness(alignments: list[R4PMVariantAlignmentResult], process_model: R4PMPetriNet) -> FitnessResult:
    return FitnessResult.model_validate(r4pm.bindings.compute_fitness(process_model, alignments))


def compute_aggregated(
    variant_alignments: list[VariantAlignmentResult],
) -> Aggregated:
    total_traces = sum(v.frequency for v in variant_alignments)
    transition_stats: dict[str, dict[str, int]] = {}
    log_move_counts: dict[str, int] = {}

    for v in variant_alignments:
        result = v.result
        if "Ok" not in result:
            continue
        freq = v.frequency
        for move in result["Ok"]["moves"]:
            if "SyncMove" in move:
                t = transition_id(move["SyncMove"]["transition"])
                stats = transition_stats.setdefault(t, {"sync_fires": 0, "model_fires": 0})
                stats["sync_fires"] += freq
            elif "ModelMove" in move:
                t = transition_id(move["ModelMove"]["transition"])
                stats = transition_stats.setdefault(t, {"sync_fires": 0, "model_fires": 0})
                stats["model_fires"] += freq
            elif "LogMove" in move:
                idx = move["LogMove"]["trace_event_index"]
                activity = v.activities[idx]
                log_move_counts[activity] = log_move_counts.get(activity, 0) + freq

    return Aggregated(
        total_traces=total_traces,
        transition_stats={k: TransitionStat(**v) for k, v in transition_stats.items()},
        log_move_counts=log_move_counts,
    )


def compute_alignments(ocel: OCEL, object_type: str, petri_net: PetriNet | None):
    (proj_id, process_model) = preprocessing(ocel, object_type, petri_net)
    options: AlignmentOptions = {
        "cost_fn": {
            "log_move_cost": 1,
            "model_move_cost": 1,
            "silent_move_cost": 0,
            "sync_move_cost": 0,
        }
    }
    try:
        raw_alignments = variant_alignment(proj_id, process_model, options)
        fitness = compute_fitness(raw_alignments, process_model)
    except Exception as e:
        raise AlignmentComputationError(str(e), traceback.format_exc()) from e
    alignments = [VariantAlignmentResult.model_validate(a) for a in raw_alignments]
    aggregated = compute_aggregated(alignments)
    return AlignmentsResponse(
        net=convert_net(process_model),
        variant_alignments=alignments,
        fitness=fitness,
        aggregated=aggregated,
    )
