import React from "react";

interface SandboxedHtmlFrameProps {
  htmlContent: string;
  title: string;
}

export const SandboxedHtmlFrame: React.FC<SandboxedHtmlFrameProps> = ({ htmlContent, title }) => {
  return (
    <div className="w-full h-full min-h-[450px] bg-white rounded-lg overflow-hidden border border-surface-200">
      <iframe
        title={title}
        srcDoc={htmlContent}
        sandbox="allow-scripts"
        className="w-full h-full min-h-[500px] border-none"
      />
    </div>
  );
};
