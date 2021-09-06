import React from "react";
import Editor from "./Editor";
import Grid from "./Grid";
import classnames from "classnames";

import { Functions, Toc as FieldNames, Settings } from "@material-ui/icons";
import slice, {
  useModalIsShown,
  useSidebarContext,
  useSelectedInstance,
  useInstances,
} from "../queryBuilderSlice";
import { useAppDispatch } from "../../../store";
import { SidebarOption } from "../types";
import {
  populateInstanceList,
  populateIssueSchema,
  populateFunctionList,
} from "../thunks";

import FunctionsSidebar from "./sideBar/Functions";
import FieldNamesSidebar from "./sideBar/FieldNames";
import SettingsSidebar from "./sideBar/Settings";
import AddInstance from "./modal/AddInstance";

const QueryBuilder: React.FC = () => {
  const { selected, shown } = useSidebarContext();
  const dispatch = useAppDispatch();
  const selectedInstance = useSelectedInstance();
  const instances = useInstances();

  const addInstanceModalShown = useModalIsShown("createNew");

  React.useEffect(() => {
    dispatch(populateInstanceList());
  }, [dispatch]);

  React.useEffect(() => {
    if (instances && instances.length === 0) {
      dispatch(slice.actions.showModal("createNew"));
    }
  }, [instances]);

  React.useEffect(() => {
    dispatch(populateIssueSchema());
  }, [dispatch, selectedInstance]);

  function onToggleSidebar(name: SidebarOption) {
    if (shown && selected === name) {
      dispatch(slice.actions.hideSidebar());
    } else {
      dispatch(slice.actions.showSidebar(name));
    }
  }

  React.useEffect(() => {
    dispatch(populateFunctionList());
  }, []);

  return (
    <div className="queryBuilder">
      <div className="body">
        <div className="sideBar">
          <Settings
            onClick={() => onToggleSidebar("settings")}
            className={classnames({
              selected: shown && selected === "settings",
            })}
          />
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
          {/*
          <Code
            onClick={() => onToggleSidebar("code")}
            className={classnames({ selected: shown && selected === "code" })}
          />
          */}
        </div>
        <div
          className={classnames("sidebarContainer", {
            displayed: shown,
          })}
        >
          <div className="sidebarContainerInner">
            {selected === "settings" && <SettingsSidebar />}
            {selected === "fieldnames" && <FieldNamesSidebar />}
            {selected === "functions" && <FunctionsSidebar />}
            {selected === "code" && <div>Code</div>}
          </div>
        </div>
        <Editor />
        <Grid />
      </div>
      {addInstanceModalShown && <AddInstance />}
    </div>
  );
};

export default QueryBuilder;
