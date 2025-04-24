import React from 'react';
import { Routes, Route } from 'react-router-dom';
import QueryForm      from './components/QueryForm';
import Loader         from './components/Loader';
import Visualizations from './components/Visualizations';

const App: React.FC = () => (
  <Routes>
    <Route path="/"            element={<QueryForm />} />
    <Route path="/loader"      element={<Loader />} />
    <Route path="/visualizations" element={<Visualizations />} />
  </Routes>
);

export default App;
