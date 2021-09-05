import React from "react";

import { Search as SearchIcon } from "@material-ui/icons";

export interface Props {
  placeholder?: string;
  onChange: (text: string) => void;
}

const Search: React.FC<Props> = ({ onChange, placeholder = "Search" }) => {
  return (
    <div className="searchBar">
      <input
        type="search"
        placeholder={placeholder}
        onChange={(evt) => onChange(evt.target.value)}
      />
      <SearchIcon />
    </div>
  );
};

export default Search;
