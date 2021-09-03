import React from "react";

import DataGrid from "react-data-grid";
import { useGridContext } from "../queryBuilderSlice";

const Grid: React.FC = () => {
  const gridContext = useGridContext();

  return (
    <div className="grid">
      <DataGrid columns={gridContext.columns} rows={gridContext.rows} />
    </div>
  );
};

export default Grid;
