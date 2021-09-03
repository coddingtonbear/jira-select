import React from "react";
import Editor from "./Editor";

const QueryBuilder: React.FC = () => {
  return (
    <div className="queryBuilder">
      <div className="toolbar"></div>
      <div className="body">
        <div className="sideBar"></div>
        <Editor />
        <div className="grid"></div>
      </div>
    </div>
  );
};

export default QueryBuilder;
