import { Save } from "@material-ui/icons";
import React from "react";
import { useAppDispatch } from "../../../../store";
import LoadingIndicator from "../LoadingIndicator";
import { setupInstance } from "../../thunks";
import slice from "../../queryBuilderSlice";

import Modal from "./Modal";

const AddInstance: React.FC = () => {
  const [name, setName] = React.useState<string>("");
  const [username, setUsername] = React.useState<string>("");
  const [password, setPassword] = React.useState<string>("");
  const [url, setUrl] = React.useState<string>("");

  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string>();

  const dispatch = useAppDispatch();

  const onSave = () => {
    setLoading(true);
    setError(undefined);
    dispatch(
      setupInstance({
        username,
        password,
        name,
        url,
      })
    ).then((result) => {
      setLoading(false);
      if (result.meta.requestStatus === "rejected") {
        setError("Could not connect to Jira using this information.");
      } else {
        dispatch(slice.actions.closeModal("createNew"));
      }
    });
  };

  return (
    <Modal className="add-instance">
      <h3>We need a little information from you: </h3>

      <div className="form">
        <div className="field">
          <label>Instance Url</label>
          <p>
            The URL you would go to for accessing Jira via your web browser.
          </p>
          <input
            type="url"
            value={url}
            placeholder="https://jira.mycompany.com/"
            onChange={(evt) => setUrl(evt.target.value)}
          />
        </div>
        <div className="field">
          <label>Username</label>
          <p>The username you would log-in to your Jira instance using.</p>
          <input
            type="text"
            value={username}
            onChange={(evt) => setUsername(evt.target.value)}
          />
        </div>
        <div className="field">
          <label>Password</label>
          <p>
            The password for your account above, or an API token. This will be
            stored in your system keyring.
          </p>
          <input
            type="password"
            value={password}
            onChange={(evt) => setPassword(evt.target.value)}
          />
        </div>
        <div className="field">
          <label>Friendly Name</label>
          <p>A name you can use for this connection.</p>
          <input
            type="text"
            value={name}
            placeholder="My Company's Jira"
            onChange={(evt) => setName(evt.target.value)}
          />
        </div>
        {loading && <LoadingIndicator />}
        {!loading && (
          <>
            <div className="buttons">
              <button
                disabled={!(url && username && password)}
                onClick={onSave}
              >
                <label>Save Settings</label>
                <Save />
              </button>
            </div>
            {error && <p className="error">{error}</p>}
          </>
        )}
      </div>
    </Modal>
  );
};

export default AddInstance;
