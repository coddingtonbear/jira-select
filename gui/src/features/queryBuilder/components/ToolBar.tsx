import React from "react";

import { useAppDispatch } from "../../../store";
import { useInstances, useSelectedInstance } from "../queryBuilderSlice";
import { populateInstanceList } from "../thunks";
import slice from "../queryBuilderSlice";

const ToolBar: React.FC = () => {
  const instances = useInstances();
  const selectedInstance = useSelectedInstance();

  const dispatch = useAppDispatch();

  React.useEffect(() => {
    dispatch(populateInstanceList());
  }, []);

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
