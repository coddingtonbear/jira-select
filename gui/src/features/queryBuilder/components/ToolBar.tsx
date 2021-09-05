import React from "react";

import { useAppDispatch } from "../../../store";
import { useInstances, useSelectedInstance } from "../queryBuilderSlice";
import { populateInstanceList, populateIssueSchema } from "../thunks";
import slice from "../queryBuilderSlice";

const ToolBar: React.FC = () => {
  const instances = useInstances();
  const selectedInstance = useSelectedInstance();

  const dispatch = useAppDispatch();

  React.useEffect(() => {
    dispatch(populateInstanceList());
  }, [dispatch]);

  React.useEffect(() => {
    dispatch(populateIssueSchema());
  }, [dispatch, selectedInstance]);

  return (
    <div className="toolbar">
      <div className="instance-selector">
        <select
          value={selectedInstance}
          onChange={(evt) =>
            dispatch(slice.actions.setSelectedInstance(evt.target.value))
          }
        >
          {selectedInstance === undefined && <option></option>}
          {instances.map((instance) => {
            return (
              <option value={instance.name} key={instance.name}>
                {instance.name} ({instance.url})
              </option>
            );
          })}
        </select>
      </div>
    </div>
  );
};

export default ToolBar;
