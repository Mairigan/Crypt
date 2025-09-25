import React, { useState } from 'react';
import axios from 'axios';
import '../styles/Contact.css';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [status, setStatus] = useState({ message: '', type: '' });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setStatus({ message: 'Sending...', type: 'info' });
      
      const response = await axios.post('/api/contact', formData);
      
      setStatus({ message: response.data.message, type: 'success' });
      setFormData({ name: '', email: '', message: '' });
    } catch (error) {
      setStatus({ 
        message: error.response?.data?.error || 'Failed to send message', 
        type: 'error' 
      });
    }
  };

  return (
    <section className="contact-page">
      <div className="container">
        <div className="section-title">
          <h2>Contact Us</h2>
          <p>We're here to help you with any questions or support needs</p>
        </div>
        
        <div className="contact-content">
          <div className="contact-info">
            <div className="contact-card">
              <div className="contact-icon">
                <i className="fas fa-envelope"></i>
              </div>
              <h3>Email Support</h3>
              <p>Get help directly from our support team</p>
              <a href="mailto:contactsupport@raydi.com" className="contact-link">
                contactsupport@raydi.com
              </a>
            </div>
            
            <div className="contact-card">
              <div className="contact-icon">
                <i className="fab fa-telegram"></i>
              </div>
              <h3>Telegram Support</h3>
              <p>Message us directly on Telegram</p>
              <a href="https://t.me/ray_diu" className="contact-link">
                @ray_diu
              </a>
            </div>
            
            <div className="contact-card">
              <div className="contact-icon">
                <i className="fas fa-comments"></i>
              </div>
              <h3>Community Chat</h3>
              <p>Join our community for help and discussions</p>
              <a href="https://t.me/SolSniperProCommunity" className="contact-link">
                Join Telegram Group
              </a>
            </div>
          </div>
          
          <div className="contact-form-container">
            <h3>Send us a Message</h3>
            <form className="contact-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Your Name</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="email">Your Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="message">Your Message</label>
                <textarea
                  id="message"
                  name="message"
                  rows="5"
                  value={formData.message}
                  onChange={handleChange}
                  required
                ></textarea>
              </div>
              
              <button type="submit" className="cta-button">Send Message</button>
              
              {status.message && (
                <div className={`status-message ${status.type}`}>
                  {status.message}
                </div>
              )}
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Contact;
