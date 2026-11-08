import React from "react";
import { Composition } from "remotion";
import { Explainer, totalFrames } from "./Explainer";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Explainer"
        component={Explainer}
        durationInFrames={totalFrames("en")}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ lang: "en" as const }}
      />
      <Composition
        id="ExplainerHE"
        component={Explainer}
        durationInFrames={totalFrames("he")}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ lang: "he" as const }}
      />
    </>
  );
};
