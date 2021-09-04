import React from "react";
import Editor from "./Editor";
import Grid from "./Grid";

const QueryBuilder: React.FC = () => {
  return (
    <div className="queryBuilder">
      <div className="toolbar"></div>
      <div className="body">
        <div className="sideBar"></div>
        <Editor />
        <Grid />
      </div>
    </div>
  );
};

export default QueryBuilder;
