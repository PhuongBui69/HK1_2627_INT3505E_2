from flask import Flask, request, jsonify

app = Flask(__name__)


# Mock data\
posts = [
    {"id": 1, "title": "REST API Guidelines", "content": "Learn how to build standard RESTful APIs", "author_id": 1},
    {"id": 2, "title": "Flask Routing", "content": "Flask makes routing easy.", "author_id": 2}
]

# --- 4. Triển khai Flask routes cho collection /posts ---

# 4.1 Lấy danh sách bài viết (GET collection)
@app.route('/api/v1/posts', methods=['GET'])
def get_posts():
    # Thực tế sẽ hỗ trợ query params (pagination: ?page=1&limit=10, filtering: ?author_id=1)
    return jsonify({
        "status": "success",
        "data": posts
    }), 200

# 4.2 Tạo bài viết mới (POST collection)
@app.route('/api/v1/posts', methods=['POST'])
def create_post():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Missing JSON payload"}), 400
    
    data = request.get_json()
    
    # Validate payload
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({
            "status": "error", 
            "message": "Missing required fields (title, content)"
        }), 400
        
    new_post = {
        "id": len(posts) + 1,
        "title": data['title'],
        "content": data['content'],
        "author_id": data.get('author_id', 1)
    }
    posts.append(new_post)
    
    return jsonify({
        "status": "success",
        "data": new_post
    }), 201 # HTTP 201: Created

# 4.3 Lấy thông tin chi tiết một bài viết (GET item)
@app.route('/api/v1/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        return jsonify({"status": "error", "message": "Post not found"}), 404
        
    return jsonify({
        "status": "success",
        "data": post
    }), 200

# 4.4 Cập nhật bài viết (PUT/PATCH item)
@app.route('/api/v1/posts/<int:post_id>', methods=['PUT', 'PATCH'])
def update_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        return jsonify({"status": "error", "message": "Post not found"}), 404
        
    if not request.is_json:
        return jsonify({"status": "error", "message": "Missing JSON payload"}), 400
        
    data = request.get_json()
    
    # Cập nhật các trường
    post['title'] = data.get('title', post['title'])
    post['content'] = data.get('content', post['content'])
    
    return jsonify({
        "status": "success",
        "data": post
    }), 200

# 4.5 Xóa bài viết (DELETE item)
@app.route('/api/v1/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    global posts
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        return jsonify({"status": "error", "message": "Post not found"}), 404
        
    posts = [p for p in posts if p['id'] != post_id]
    
    # Thường DELETE thành công sẽ trả về status code 204 (No Content)
    return '', 204


if __name__ == '__main__':
    app.run(debug=True, port=5000)
