import { Provider } from "react-redux";
import "./App.scss";

import QueryBuilder from "./features/queryBuilder/components/QueryBuilder";
import { store } from "./store";

function App() {
  return (
    <Provider store={store}>
      <QueryBuilder />
    </Provider>
  );
}

export default App;
