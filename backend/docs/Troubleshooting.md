# TROUBLESHOOTING 
>Ghi các vấn đề khi xây dựng dự án

### 1.  Section_queue không lưu đúng title của các mục: 
#### Problem: Giả sử section_id
- 1 xuất hiện 2 nơi trong PDF => section_id: 1 đầu tiên sẽ bị ghi đè => Nếu build_context_headers cho toàn bộ chunks sau khi đã tạo chunks xong thì section_id: 1 sẽ không còn đúng
#### Giải pháp: 
- thay vì build lại sau khi đã tạo xong chunks thì tạo luôn cho từng chunk lúc tạo chunk đó. 


### 2. Context khi dùng vector search không khớp với query
#### Problem: Sử dụng 2 loại model embedding cho 2 tác vụ
- 1. Sử dụng model BGE từ Hf_API khi indexing vào Elasticsearch
- 2. Sử dụng openai hoặc google embedding model khi Elastichsearch inference
>Dẫn đến 2 vector embedding khác nhau => context không chuẩn
#### Giải pháp: Chỉ sử dụng 1 embedding model cho 2 tác vụ

