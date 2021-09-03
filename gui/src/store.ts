import { configureStore, combineReducers } from "@reduxjs/toolkit";
import devToolsEnhancer from "remote-redux-devtools";
import { useDispatch } from "react-redux";

import queryBuilderSlice from "./features/queryBuilder/queryBuilderSlice";

const rootReducer = combineReducers({
  queryEditor: queryBuilderSlice.reducer,
});

export const store = configureStore({
  reducer: rootReducer,
  devTools: false,
  enhancers: [
    devToolsEnhancer({
      realtime: true,
      port: 24723,
    }),
  ],
});

export const { actions: queryBuilderActions } = queryBuilderSlice;

export type RootState = ReturnType<typeof rootReducer>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = (): AppDispatch => useDispatch<AppDispatch>();
