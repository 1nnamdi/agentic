import React from "react";
import '../index.css';

const Loading = (props) => {
  if (props.loading) {
      return (
          <div className="slider">
              <div className="moving-line" />
          </div>
      );
  }
  return null; // Return null if not loading
};

export { Loading };