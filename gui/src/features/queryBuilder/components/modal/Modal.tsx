import classNames from "classnames";
import React from "react";
import { useAppDispatch } from "../../../../store";
import slice from "../../queryBuilderSlice";

export interface Props {
  className?: string;
}

const Modal: React.FC<Props> = ({ children, className }) => {
  const dispatch = useAppDispatch();

  return (
    <div
      className="modal-background"
      onClick={() => dispatch(slice.actions.closeModal())}
    >
      <div
        className={classNames("modal", className)}
        onClick={(evt) => {
          evt.stopPropagation();
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default Modal;
