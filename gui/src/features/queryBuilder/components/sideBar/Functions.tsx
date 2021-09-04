import React from "react";
import {
  getFunctions,
  JiraSelectFunction,
} from "../../../../jira_select_client";
import { useAppDispatch } from "../../../../store";
import slice from "../../queryBuilderSlice";

const Functions: React.FC = () => {
  const [functions, setFunctions] = React.useState<JiraSelectFunction[]>([]);
  const [error, setError] = React.useState<string>();

  const dispatch = useAppDispatch();

  React.useEffect(() => {
    getFunctions()
      .then((fns) => setFunctions(fns))
      .catch((msg) => setError(msg));
  }, []);

  function onClickFunction(name: string) {
    dispatch(slice.actions.insertTextAtCursor(name));
  }

  return (
    <div className="functions">
      <h2>Functions</h2>
      {error && <div>{error}</div>}
      {functions.map((fn) => {
        return (
          <div className="function" key={fn.dotpath + "." + fn.name}>
            <div className="name">
              <span className="name" onClick={() => onClickFunction(fn.name)}>
                {fn.name}
              </span>
              <span className="signature">{fn.signature}</span>
              <span className="module">{fn.dotpath}</span>
            </div>
            <div className="description">{fn.description}</div>
          </div>
        );
      })}
    </div>
  );
};

export default Functions;
