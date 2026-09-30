TOKEN=$(python3 /tmp/bl_tok.py)
echo "== sessions =="
curl -s "http://127.0.0.1:25130/sessions?token=$TOKEN" | head -c 3000
echo
echo "== active =="
curl -s "http://127.0.0.1:25130/active?token=$TOKEN" | head -c 2000
