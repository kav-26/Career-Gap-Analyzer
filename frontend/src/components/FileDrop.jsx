import { useRef, useState } from "react";

const OK = /\.(pdf|docx|txt)$/i;

export default function FileDrop({ files, onChange, multiple = true, hint }) {
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);

  function add(list) {
    const picked = Array.from(list).filter((f) => OK.test(f.name));
    if (!picked.length) return;
    onChange(multiple ? [...files, ...picked] : [picked[0]]);
  }

  function remove(index) {
    onChange(files.filter((_, i) => i !== index));
  }

  return (
    <div>
      <div
        className={"drop" + (over ? " over" : "")}
        onClick={() => inputRef.current && inputRef.current.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          add(e.dataTransfer.files);
        }}
      >
        <p>
          <strong>Click to choose</strong> or drag files here
        </p>
        <p className="muted">{hint}</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          multiple={multiple}
          hidden
          onChange={(e) => {
            add(e.target.files);
            e.target.value = "";
          }}
        />
      </div>
      {files.length > 0 && (
        <ul className="filelist">
          {files.map((f, i) => (
            <li key={f.name + i}>
              <span>{f.name}</span>
              <button className="link" onClick={() => remove(i)}>
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
