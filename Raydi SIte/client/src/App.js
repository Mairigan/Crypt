import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import Features from './pages/Features';
import HowItWorks from './pages/HowItWorks';
import Community from './pages/Community';
import Contact from './pages/Contact';
import './styles/App.css';

const routes = [
  { path: "/", element: <Home /> },
  { path: "/features", element: <Features /> },
  { path: "/how-it-works", element: <HowItWorks /> },
  { path: "/community", element: <Community /> },
  { path: "/contact", element: <Contact /> },
];

function App() {
  return (
    <Router>
      <section id="app">
        <Header />
        <main>
          <Routes>
            {routes.map((route, idx) => (
              <Route key={idx} path={route.path} element={route.element} />
            ))}
          </Routes>
        </main>
        <Footer />
      </section>
    </Router>
  );
}

export default App;
