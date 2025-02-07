# Use the official Node.js image
FROM node:16 AS build

WORKDIR /app

# Copy the React app source code
COPY . .

# Install dependencies and build the app
RUN npm install && npm run build

# Use a simple HTTP server to serve the React app
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

# Expose the port for the React app
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]