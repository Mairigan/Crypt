import { Link } from 'react-router-dom';
import { FaTelegram } from 'react-icons/fa';
import '../styles/Home.css';

const Home = () => {
  return (
    <section className="hero">
      <div className="container">
        <h1>Seize The Alpha. First.</h1>
        <p>
          SolSniper Pro is the most advanced Telegram bot designed to give you the ultimate advantage in sniping new launches on Solana.<br />
          Get in first, before the crowd.
        </p>
          <a
            href="https://t.me/Raydi_Bot"
            className="cta-button"
            target="_blank"
            rel="noopener noreferrer"
          >
            <FaTelegram /> Start Sniping on Telegram
          </a>
          <Link to="/features" className="secondary-button">Explore Features</Link>
      </div>
    </section>
  );
};

export default Home;
