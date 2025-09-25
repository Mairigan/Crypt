const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
      fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"]
    }
  }
}));

// Rate limiting
const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use(generalLimiter);

// Custom rate limiter for sensitive routes
const contactLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // stricter limit for contact endpoint
  message: "Too many requests from this IP, please try again after 15 minutes."
});

// API Routes
// Serve React build in production
if (process.env.NODE_ENV === 'production') {
  // Serve static assets from the 'public' folder for general static files (e.g., images, favicon, etc.)
  app.use(express.static(path.join(__dirname, 'public')));

  // Serve React build static files from '../client/build'.
  app.use(express.static(path.join(__dirname, '../client/build')));

  // For any route not handled by the above, serve React's index.html (SPA fallback)
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../client/build', 'index.html'));
  });
}

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
