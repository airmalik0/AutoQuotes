import { useState } from 'react';
import PhotoUpload from '../components/PhotoUpload';
import { postRequest } from '../api/client';

interface PartDetailsProps {
  carData: { brand: string; model: string; year: number };
}

type PartType = 'original' | 'duplicate' | 'used';

const PART_TYPE_LABELS: Record<PartType, string> = {
  original: 'Оригинал',
  duplicate: 'Дубликат',
  used: 'Б/У',
};

export default function PartDetails({ carData }: PartDetailsProps) {
  const [description, setDescription] = useState('');
  const [partType, setPartType] = useState<PartType | ''>('');
  const [photos, setPhotos] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = description.trim().length >= 3 && partType !== '';

  const handleSubmit = async () => {
    if (!canSubmit || submitting) return;

    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append('brand', carData.brand);
      fd.append('model', carData.model);
      fd.append('year', String(carData.year));
      fd.append('description', description.trim());
      fd.append('part_type', partType);
      fd.append('init_data', window.Telegram.WebApp.initData);
      photos.forEach((photo) => fd.append('photos', photo));

      await postRequest(fd);
      window.Telegram.WebApp.close();
    } catch {
      setSubmitting(false);
      alert('Ошибка при отправке. Попробуйте ещё раз.');
    }
  };

  return (
    <div className="page">
      <h2>Описание запчасти</h2>
      <p className="car-summary">
        {carData.brand} {carData.model}, {carData.year}
      </p>

      <label className="field-label">Описание</label>
      <textarea
        placeholder="Опишите нужную запчасть (мин. 3 символа)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={4}
      />

      <label className="field-label">Тип запчасти</label>
      <div className="radio-group">
        {(Object.keys(PART_TYPE_LABELS) as PartType[]).map((pt) => (
          <label key={pt} className="radio-label">
            <input
              type="radio"
              name="part_type"
              value={pt}
              checked={partType === pt}
              onChange={() => setPartType(pt)}
            />
            <span>{PART_TYPE_LABELS[pt]}</span>
          </label>
        ))}
      </div>

      <label className="field-label">Фото (до 3)</label>
      <PhotoUpload photos={photos} onChange={setPhotos} />

      <button
        className="btn-primary"
        disabled={!canSubmit || submitting}
        onClick={handleSubmit}
      >
        {submitting ? (
          <span className="spinner" />
        ) : (
          'Отправить \u2713'
        )}
      </button>
    </div>
  );
}
