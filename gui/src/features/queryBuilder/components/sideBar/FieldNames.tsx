import React from "react";

import { JiraSelectSchemaItem } from "../../../../jira_select_client";
import { useAppDispatch } from "../../../../store";
import slice, {
  useIssueSchema,
  useSelectedInstance,
} from "../../queryBuilderSlice";
import { populateIssueSchema } from "../../thunks";
import LoadingIndicator from "../LoadingIndicator";

const FieldNames: React.FC = () => {
  const availableIssueSchemaItems = useIssueSchema();
  const selectedInstance = useSelectedInstance();

  const [schema, setSchema] = React.useState<JiraSelectSchemaItem[]>([]);
  const [searchText, setSearchText] = React.useState<string>("");

  const dispatch = useAppDispatch();

  React.useEffect(() => {
    dispatch(slice.actions.clearIssueSchema());
    dispatch(populateIssueSchema());
  }, [selectedInstance]);

  React.useEffect(() => {
    const filteredSchema: JiraSelectSchemaItem[] = [];

    if (availableIssueSchemaItems === undefined) {
      setSchema([]);
      return;
    }
    if (searchText.length === 0) {
      setSchema(availableIssueSchemaItems);
      return;
    }
    for (const fn of availableIssueSchemaItems) {
      const searchFields: string[] = [fn.id, fn.type, fn.description ?? ""];
      for (const field of searchFields) {
        if (field.toLowerCase().includes(searchText.toLowerCase())) {
          filteredSchema.push(fn);
          break;
        }
      }
    }

    setSchema(filteredSchema);
  }, [searchText, availableIssueSchemaItems]);

  function onClickFunction(name: string) {
    dispatch(slice.actions.insertTextAtCursor(name));
  }

  return (
    <div className="schema">
      <h2>Issue Schema</h2>
      <input
        type="search"
        placeholder="Search"
        onChange={(evt) => setSearchText(evt.target.value)}
      />
      <div className="schema-list">
        {selectedInstance ? (
          <>
            {availableIssueSchemaItems === undefined && <LoadingIndicator />}
            {schema.map((fn) => {
              return (
                <div className="field" key={fn.id}>
                  <div className="id" onClick={() => onClickFunction(fn.id)}>
                    {fn.id}
                  </div>
                  <div className="type">{fn.type}</div>
                  <div className="description">{fn.description}</div>
                </div>
              );
            })}
          </>
        ) : (
          <p>No Instance selected</p>
        )}
      </div>
    </div>
  );
};

export default FieldNames;
