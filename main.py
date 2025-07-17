from flask import Flask, request, render_template, redirect
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

latest_result = {}

@app.route('/')
def index():
    return render_template("upload.html")

@app.route('/analyze', methods=['POST'])
def analyze():
    global latest_result

    if 'file' not in request.files:
        return "يرجى اختيار ملف", 400

    file = request.files['file']
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return f"خطأ في قراءة الملف: {e}", 400

    if 'amount' not in df.columns or 'category' not in df.columns:
        return "الملف يجب أن يحتوي على amount و category", 400

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df.dropna(subset=['amount'], inplace=True)

    income = df[df['amount'] > 0]['amount'].sum()
    expenses = df[df['amount'] < 0].copy()
    expenses['amount'] = expenses['amount'].abs()

    category_expenses = expenses.groupby('category')['amount'].sum().reset_index().to_dict(orient='records')
    total_expense = expenses['amount'].sum()

    danger_percent = round((total_expense / income) * 100, 2) if income > 0 else 100.0

    if danger_percent >= 100:
        risk = "🔴 خطر مرتفع"
    elif danger_percent >= 70:
        risk = "🟠 خطر متوسط"
    else:
        risk = "🟢 خطر منخفض"

    latest_result = {
        "total_income": round(income, 2),
        "category_expenses": category_expenses,
        "danger_percent": danger_percent,
        "risk_level": risk
    }

    return render_template("success.html", result=latest_result)

@app.route('/latest', methods=['GET'])
def latest():
    return latest_result if latest_result else {"message": "لا يوجد تحليل بعد"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
