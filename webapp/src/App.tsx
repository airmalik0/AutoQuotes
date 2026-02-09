import { useState } from 'react';
import CarSelect from './pages/CarSelect';
import PartDetails from './pages/PartDetails';

interface CarData {
  brand: string;
  model: string;
  year: number;
}

export default function App() {
  const [carData, setCarData] = useState<CarData | null>(null);

  if (!carData) {
    return <CarSelect onNext={setCarData} />;
  }

  return <PartDetails carData={carData} />;
}
