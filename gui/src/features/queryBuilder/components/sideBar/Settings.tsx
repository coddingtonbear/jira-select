import React from "react";

import { useAppDispatch } from "../../../../store";
import { useInstances, useSelectedInstance } from "../../queryBuilderSlice";
import slice from "../../queryBuilderSlice";
import { Add } from "@material-ui/icons";

const Settings: React.FC = () => {
  const instances = useInstances();
  const selectedInstance = useSelectedInstance();

  const dispatch = useAppDispatch();

  return (
    <div className="settings">
      <h2>Configuration</h2>

      <div className="setting">
        <label>Jira Instance:</label>
        <div className="instance-selector">
          <select
            value={selectedInstance}
            onChange={(evt) =>
              dispatch(slice.actions.setSelectedInstance(evt.target.value))
            }
          >
            {instances &&
              instances.map((instance) => {
                return (
                  <option value={instance.name} key={instance.name}>
                    {instance.name} ({instance.url})
                  </option>
                );
              })}
          </select>
        </div>

        <div className="instance-buttons">
          <button
            onClick={() => dispatch(slice.actions.showModal("createNew"))}
          >
            <Add />
            <label>Add another instance</label>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
