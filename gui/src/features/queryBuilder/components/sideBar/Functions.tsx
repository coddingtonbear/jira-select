import React from "react";

import { JiraSelectFunction } from "../../../../jira_select_client";
import { useAppDispatch } from "../../../../store";
import slice, { useFunctionList } from "../../queryBuilderSlice";
import { populateFunctionList } from "../../thunks";
import LoadingIndicator from "../LoadingIndicator";

const Functions: React.FC = () => {
  const availableFunctions = useFunctionList();

  const [functions, setFunctions] = React.useState<JiraSelectFunction[]>([]);
  const [searchText, setSearchText] = React.useState<string>("");

  const dispatch = useAppDispatch();

  React.useEffect(() => {
    dispatch(populateFunctionList());
  }, []);

  React.useEffect(() => {
    const filteredFunctions: JiraSelectFunction[] = [];

    if (availableFunctions === undefined) {
      setFunctions([]);
      return;
    }
    if (searchText.length === 0) {
      setFunctions(availableFunctions);
      return;
    }
    for (const fn of availableFunctions) {
      const searchFields: string[] = [
        fn.description,
        fn.dotpath,
        fn.name,
        fn.signature ?? "",
      ];
      for (const field of searchFields) {
        if (field.toLowerCase().includes(searchText.toLowerCase())) {
          filteredFunctions.push(fn);
          break;
        }
      }
    }

    setFunctions(filteredFunctions);
  }, [searchText, availableFunctions]);

  function onClickFunction(name: string) {
    dispatch(slice.actions.insertTextAtCursor(name));
  }

  return (
    <div className="functions">
      <h2>Functions</h2>
      <input
        type="search"
        placeholder="Search"
        onChange={(evt) => setSearchText(evt.target.value)}
      />
      <div className="functions-list">
        {availableFunctions === undefined && <LoadingIndicator />}
        {functions.map((fn) => {
          return (
            <div className="function" key={fn.dotpath + "." + fn.name}>
              <div className="name">
                <span className="name" onClick={() => onClickFunction(fn.name)}>
                  {fn.name}
                </span>
                <span className="signature">{fn.signature}</span>
              </div>
              <div className="module">{fn.dotpath}</div>
              <div className="description">{fn.description}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Functions;
