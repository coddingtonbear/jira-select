import React from "react";
import Editor from "./Editor";
import Grid from "./Grid";
import classnames from "classnames";

import { Functions, Code, Toc as FieldNames } from "@material-ui/icons";
import slice, { useSidebarContext } from "../queryBuilderSlice";
import { useAppDispatch } from "../../../store";
import { SidebarOption } from "../types";

import FunctionsSidebar from "./sideBar/Functions";

const QueryBuilder: React.FC = () => {
  const { selected, shown } = useSidebarContext();
  const dispatch = useAppDispatch();

  function onToggleSidebar(name: SidebarOption) {
    if (shown && selected === name) {
      dispatch(slice.actions.hideSidebar());
    } else {
      dispatch(slice.actions.showSidebar(name));
    }
  }

  return (
    <div className="queryBuilder">
      <div className="toolbar"></div>
      <div className="body">
        <div className="sideBar">
          <FieldNames
            onClick={() => onToggleSidebar("fieldnames")}
            className={classnames({
              selected: shown && selected === "fieldnames",
            })}
          />
          <Functions
            onClick={() => onToggleSidebar("functions")}
            className={classnames({
              selected: shown && selected === "functions",
            })}
          />
          <Code
            onClick={() => onToggleSidebar("code")}
            className={classnames({ selected: shown && selected === "code" })}
          />
        </div>
        <div
          className={classnames("sidebarContainer", {
            displayed: shown,
          })}
        >
          {selected === "fieldnames" && <div>Fieldnames</div>}
          {selected === "functions" && <FunctionsSidebar />}
          {selected === "code" && <div>Code</div>}
        </div>
        <Editor />
        <Grid />
      </div>
    </div>
  );
};

export default QueryBuilder;
