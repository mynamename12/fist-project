from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import pandas as pd

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
        advice = "أنت تصرف أكثر من دخلك! راجع مصروفاتك فوراً."
    elif danger_percent >= 70:
        risk = "🟠 خطر متوسط"
        advice = "مصروفاتك مرتفعة، حاول تقليلها لتفادي الخطر."
    else:
        risk = "🟢 خطر منخفض"
        advice = "وضعك المالي مستقر، استمر على هذا النهج."

    latest_result = {
        "total_income": round(income, 2),
        "category_expenses": category_expenses,
        "danger_percent": danger_percent,
        "risk_level": risk,
        "advice": advice
    }

    return render_template("success.html", result=latest_result)

@app.route('/latest', methods=['GET'])
def latest():
    if not latest_result:
        return jsonify({"message": "لا يوجد تحليل بعد"})

    # تحويل الأرقام لنوع يقبل JSON
    safe_result = {
        "total_income": float(latest_result["total_income"]),
        "category_expenses": [
            {
                "category": str(item["category"]),
                "amount": float(item["amount"])
            }
            for item in latest_result["category_expenses"]
        ],
        "danger_percent": float(latest_result["danger_percent"]),
        "risk_level": str(latest_result["risk_level"]),
        "advice": str(latest_result.get("advice", ""))
    }

    return jsonify(safe_result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
