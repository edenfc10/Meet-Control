FROM node:20-alpine

WORKDIR /app

# העתק את כל הקוד כולל node_modules שכבר קיים
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
