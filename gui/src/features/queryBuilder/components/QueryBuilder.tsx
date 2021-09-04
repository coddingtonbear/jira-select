import React from "react";
import Editor from "./Editor";
import Grid from "./Grid";

import { Functions, Code, Toc as FieldNames } from "@material-ui/icons";

const QueryBuilder: React.FC = () => {
  return (
    <div className="queryBuilder">
      <div className="toolbar"></div>
      <div className="body">
        <div className="sideBar">
          <FieldNames />
          <Functions />
          <Code />
        </div>
        <Editor />
        <Grid />
      </div>
    </div>
  );
};

export default QueryBuilder;
