import "@r4pm/components/styles.css";
import { Box, Button, LoadingOverlay, Tabs, Stack, Text, Group, SegmentedControl } from "@mantine/core";
import { useCurrentOcel } from "@ocelescope/core";
import type { LogAlignments } from "@r4pm/components";
import { AlignmentListViewer, Theme, AlignmentNetViewer, ViewerConfigProvider } from "@r4pm/components";
import { wasmLayout } from "@r4pm/components/rust-layout/wasm";
import { useGetAlignments, useObjectTypes } from "../api/caseCentricAlignments";
import { ResourceSelect } from "@ocelescope/resources";
import { useState } from "react";
import { keepPreviousData } from "@tanstack/react-query";
import { PlayIcon } from "lucide-react";

const AlignmentComponent = ({
  ocelId,
  objectType,
  mode
}: {
  ocelId: string;
  objectType: string;
  mode: string;
}) => {
  const [resourceId, setResourceId] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  const { data, isFetching, refetch } = useGetAlignments(ocelId,{ object_type: objectType, resource_id: resourceId },{query: {enabled: false, placeholderData: keepPreviousData, retry:false}});

  const runAlignment = async () => {
    setHasRun(true);
    await refetch();
  };

  return (
    <Box pos="relative" h="100%" style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
      <LoadingOverlay visible={isFetching} />
      <Group align="flex-end" gap="sm">
        <ResourceSelect
          label="Model"
          description="Select Process Model to align against"
          type="e8a4b93820f2f145136e404a06dceb73e074982534c39d64895eda58ab5b5dc1"
          value={resourceId}
          placeholder="Auto-Discover with Alpha +++"
          onChange={(newResourceId) => setResourceId(newResourceId as string)}
          style={{ flex: 1 }}
        />
        <Button leftSection={<PlayIcon size={16} />} onClick={runAlignment}>
          Run
        </Button>
      </Group>

      <Box style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
        {!hasRun ? (
          <Text c="dimmed" ta="center" mt="xl">
            Select a model (or leave on Auto-Discover) and press Run to compute alignments.
          </Text>
        ) : (
          data && (mode === "list" ? 
          (<AlignmentListViewer data={data as LogAlignments}/>) 
          : (
          <ViewerConfigProvider value={{ layout: wasmLayout }}>
              <AlignmentNetViewer data={data as LogAlignments} />
          </ViewerConfigProvider>))
        )}
      </Box>
    </Box>
  );
};

const Alignment = () => {
  const { id } = useCurrentOcel();
  const { data: objectTypes } = useObjectTypes(id, undefined, { query: { enabled: !!id } });
  const [mode, setMode] = useState<"list" | "net">('list');

  if (!id || !objectTypes) {
    return <LoadingOverlay visible />;
  }

  const [firstObjectType, ...otherObjectTypes] = objectTypes;
  if (!firstObjectType) {
    return null;
  }

  return (
    <>
      {otherObjectTypes.length > 0 ? (
        <Tabs defaultValue={firstObjectType} keepMounted={false} h={"100%"}>
          <Stack h="100%" gap={"xs"}>
            <Tabs.List mb="sm">
              {objectTypes.map((objectType) => (
                <Tabs.Tab key={objectType} value={objectType}>
                  {objectType}
                </Tabs.Tab>
              ))}
            </Tabs.List>
            <Stack h="100%" px="xs">
              <SegmentedControl 
                  value={mode} 
                  onChange={setMode} 
                  data={[{label: "Alignment List", value:"list"}, {label:"Alignment Net", value:"net"}]} 
                  size="xs"
                  w={280}>
              </SegmentedControl>
              {objectTypes.map((objectType) => (
                <Tabs.Panel key={objectType} value={objectType} flex={1}>
                  <AlignmentComponent ocelId={id} objectType={objectType} mode={mode} />
                </Tabs.Panel>
              ))}
            </Stack>
          </Stack>
        </Tabs>
      ) : (
        <Stack h="100%" px="xs" pt={"xs"}>
          <SegmentedControl 
                  value={mode} 
                  onChange={setMode} 
                  data={[{label: "Alignment List", value:"list"}, {label:"Alignment Net", value:"net"}]} 
                  size="xs"
                  w={280}>
          </SegmentedControl>
          <AlignmentComponent ocelId={id} objectType={firstObjectType} mode={mode} />
        </Stack>
      )}
    </>
  );
};

export default Alignment