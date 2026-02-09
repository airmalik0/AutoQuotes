import { useState } from 'react';
import { CARS, YEARS } from '../data/cars';

interface CarSelectProps {
  onNext: (data: { brand: string; model: string; year: number }) => void;
}

export default function CarSelect({ onNext }: CarSelectProps) {
  const [brand, setBrand] = useState('');
  const [model, setModel] = useState('');
  const [year, setYear] = useState('');

  const models = brand ? CARS[brand] ?? [] : [];
  const canProceed = brand && model && year;

  const handleBrandChange = (value: string) => {
    setBrand(value);
    setModel('');
  };

  return (
    <div className="page">
      <h2>Выберите автомобиль</h2>

      <label className="field-label">Марка</label>
      <select value={brand} onChange={(e) => handleBrandChange(e.target.value)}>
        <option value="">-- Выберите марку --</option>
        {Object.keys(CARS).map((b) => (
          <option key={b} value={b}>{b}</option>
        ))}
      </select>

      <label className="field-label">Модель</label>
      <select
        value={model}
        onChange={(e) => setModel(e.target.value)}
        disabled={!brand}
      >
        <option value="">-- Выберите модель --</option>
        {models.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>

      <label className="field-label">Год выпуска</label>
      <select value={year} onChange={(e) => setYear(e.target.value)}>
        <option value="">-- Выберите год --</option>
        {YEARS.map((y) => (
          <option key={y} value={y}>{y}</option>
        ))}
      </select>

      <button
        className="btn-primary"
        disabled={!canProceed}
        onClick={() => onNext({ brand, model, year: Number(year) })}
      >
        Далее →
      </button>
    </div>
  );
}
