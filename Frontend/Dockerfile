# פיתוח לוקלי בלבד — Vite dev server עם hot reload. לא מתאים לפרודאקשן.
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --no-audit --no-fund

# העתק את כל הקוד כולל node_modules שכבר קיים
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
