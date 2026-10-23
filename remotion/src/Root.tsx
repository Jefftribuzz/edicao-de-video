import { Composition, Folder } from "remotion";
import { SrMantasQM2 } from "./sr-mantas-qm2/SrMantasQM2";

export const RemotionRoot: React.FC = () => {
  return (
    <Folder name="SR-Mantas">
      <Composition
        id="SrMantasQM2"
        component={SrMantasQM2}
        durationInFrames={1574}
        fps={60}
        width={1440}
        height={2560}
      />
    </Folder>
  );
};
