import classNames from "classnames";
import React from "react";

import { JiraSelectFunction } from "../../../../jira_select_client";
import { useAppDispatch } from "../../../../store";
import slice, {
  useExpandedFunctions,
  useFunctionList,
} from "../../queryBuilderSlice";
import LoadingIndicator from "../LoadingIndicator";
import Search from "../Search";

const Functions: React.FC = () => {
  const availableFunctions = useFunctionList();
  const expandedFunctions = useExpandedFunctions();

  const [functions, setFunctions] = React.useState<JiraSelectFunction[]>([]);
  const [searchText, setSearchText] = React.useState<string>("");

  const dispatch = useAppDispatch();

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

  function onInsertFunctionName(name: string) {
    dispatch(slice.actions.insertTextAtCursor(name));
  }

  function onExpandFunction(name: string) {
    dispatch(slice.actions.toggleFunctionExpansion(name));
  }

  return (
    <div className="functions">
      <Search onChange={setSearchText} placeholder="Search functions" />
      <div className="functions-list">
        {availableFunctions === undefined && <LoadingIndicator />}
        {functions.map((fn) => {
          return (
            <div
              className={classNames("function", {
                expanded: expandedFunctions.includes(fn.name),
              })}
              key={fn.name}
              onClick={() => onExpandFunction(fn.name)}
            >
              <div className="name">
                <span
                  className="name"
                  onClick={() => onInsertFunctionName(fn.name)}
                >
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
