import socket
import subprocess
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--workplace", type=str, default="/workplace")
parser.add_argument("--port", type=int, default="8000")
args = parser.parse_args()

if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", args.port))
    server.listen(1)

    print(f"[INFO] Listening on port {args.port}...")
    def receive_all(conn, buffer_size=4096):
        data = b""
        while True:
            part = conn.recv(buffer_size)
            data += part
            if len(part) < buffer_size:
                # 如果接收的数据小于缓冲区大小，可能已经接收完毕
                break
        return data.decode()

    while True:
        conn, addr = server.accept()
        print(f"[INFO] Connection from {addr}")
        while True:
            # command = conn.recv(1024).decode()
            command = receive_all(conn)
            if not command:
                break
            
            # Execute the command
            try:
                modified_command = ["/bin/bash", "-c", command]
                process = subprocess.Popen(modified_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=args.workplace)
                output = ''
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    output += line
                    # 立即发送每一行输出
                    chunk_response = {
                        "type": "chunk",
                        "data": line
                    }
                    conn.send(json.dumps(chunk_response).encode() + b"\n")  # 添加换行符作为分隔符

                # 发送最终的完整响应
                final_response = {
                    "type": "final",
                    "status": process.poll(),
                    "result": output
                }
                conn.send(json.dumps(final_response).encode() + b"\n")
            except Exception as e:
                error_response = {
                    "type": "final",
                    "status": -1,
                    "result": f"Error running command: {str(e)}"
                }
                conn.send(json.dumps(error_response).encode() + b"\n")

            # Create a JSON response
            # response = {
            #     "status": exit_code,
            #     "result": output
            # }
            
            # # Send the JSON response
            # conn.send(json.dumps(response).encode())
        conn.close()