# Use an official Node runtime environment to compile assets
FROM node:20-alpine

WORKDIR /app

# Copy package configurations first to optimize caching speeds
COPY package*.json ./

RUN npm install

COPY . .

# Expose the Vite development/preview network port
EXPOSE 5173

# Run the frontend application
CMD ["npm", "run", "dev", "--", "--host"]