import { useRef } from 'react';

interface PhotoUploadProps {
  photos: File[];
  onChange: (photos: File[]) => void;
}

export default function PhotoUpload({ photos, onChange }: PhotoUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const addIndexRef = useRef<number>(0);

  const handleAdd = (index: number) => {
    addIndexRef.current = index;
    inputRef.current?.click();
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const updated = [...photos];
    updated[addIndexRef.current] = file;
    onChange(updated);
    e.target.value = '';
  };

  const handleRemove = (index: number) => {
    const updated = photos.filter((_, i) => i !== index);
    onChange(updated);
  };

  const slots = Array.from({ length: 3 }, (_, i) => photos[i] ?? null);

  return (
    <div className="photo-upload">
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFile}
      />
      <div className="photo-slots">
        {slots.map((file, i) => (
          <div key={i} className="photo-slot">
            {file ? (
              <div className="photo-preview">
                <img src={URL.createObjectURL(file)} alt={`Photo ${i + 1}`} />
                <button
                  type="button"
                  className="photo-remove"
                  onClick={() => handleRemove(i)}
                >
                  &times;
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="photo-add"
                onClick={() => handleAdd(i)}
              >
                +
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
