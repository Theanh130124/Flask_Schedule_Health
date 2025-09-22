// Biến toàn cục để lưu appointment_id
let currentAppointmentId = null;
let currentHealthRecordId = null;

// Hàm mở modal chuẩn đoán
function openDiagnosisModal(appointmentId, patientId, doctorId, appointmentTimeStr) {
    console.log('Mở modal chuẩn đoán cho appointment:', appointmentId);

    // Kiểm tra thời gian trước khi mở modal
    const now = new Date();
    const appointmentDate = new Date(appointmentTimeStr);
    const oneHourBefore = new Date(appointmentDate.getTime() - 60 * 60 * 1000 *24 *7);
    const oneHourAfter = new Date(appointmentDate.getTime() + 60 * 60 * 1000*24 *7);

    if (now < oneHourBefore || now > oneHourAfter) {
        alert('Chỉ có thể chuẩn đoán trong khoảng thời gian từ 1 giờ trước đến 1 giờ sau giờ hẹn khám.');
        return;
    }

    // Reset form và hiển thị loading
    document.getElementById('diagnosisForm').style.display = 'none';
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('saveDiagnosisBtn').disabled = true;

    // Lưu appointment_id
    currentAppointmentId = appointmentId;

    // Set giá trị vào form
    document.getElementById('appointmentId').value = appointmentId;
    document.getElementById('patientId').value = patientId;
    document.getElementById('doctorId').value = doctorId;

    // Hiển thị modal
    const modal = new bootstrap.Modal(document.getElementById('diagnosisModal'));
    modal.show();

    // Gọi API để lấy dữ liệu chuẩn đoán hiện tại
    fetch(`/api/get-diagnosis/${appointmentId}`)
        .then(response => response.json())
        .then(data => {
            // Ẩn loading và hiển thị form
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('diagnosisForm').style.display = 'block';

            if (data.success) {
                // Điền dữ liệu vào form nếu có
                document.getElementById('symptomsInput').value = data.symptoms || '';
                document.getElementById('diagnosisInput').value = data.diagnosis || '';
                document.getElementById('prescriptionInput').value = data.prescription || '';
                document.getElementById('notesInput').value = data.notes || '';
                currentHealthRecordId = data.record_id || null;

                // Kiểm tra có thể edit hay không
                if (!data.can_edit) {
                    const statusMessage = `Lịch hẹn này có trạng thái: ${data.appointment_status}. Chỉ có thể chuẩn đoán cho lịch hẹn đang chờ khám.`;
                    alert(statusMessage);
                    document.getElementById('saveDiagnosisBtn').disabled = true;
                    // Vô hiệu hóa các trường input
                    document.getElementById('symptomsInput').disabled = true;
                    document.getElementById('diagnosisInput').disabled = true;
                    document.getElementById('prescriptionInput').disabled = true;
                    document.getElementById('notesInput').disabled = true;
                } else {
                    document.getElementById('saveDiagnosisBtn').disabled = false;
                    // Kích hoạt các trường input
                    document.getElementById('symptomsInput').disabled = false;
                    document.getElementById('diagnosisInput').disabled = false;
                    document.getElementById('prescriptionInput').disabled = false;
                    document.getElementById('notesInput').disabled = false;
                }
            } else {
                console.error('Lỗi khi lấy dữ liệu chuẩn đoán:', data.message);
                // Reset form nếu không có dữ liệu
                document.getElementById('symptomsInput').value = '';
                document.getElementById('diagnosisInput').value = '';
                document.getElementById('prescriptionInput').value = '';
                document.getElementById('notesInput').value = '';
                currentHealthRecordId = null;
                document.getElementById('saveDiagnosisBtn').disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('diagnosisForm').style.display = 'block';
            document.getElementById('saveDiagnosisBtn').disabled = false;
        });
}

// Hàm gửi chuẩn đoán
function submitDiagnosis() {
    console.log('Gửi chuẩn đoán...');

    // Lấy dữ liệu từ form
    const formData = new FormData(document.getElementById('diagnosisForm'));

    // Chuyển thành JSON
    const jsonData = {};
    for (let [key, value] of formData.entries()) {
        jsonData[key] = value;
    }

    // Thêm record_id nếu có
    if (currentHealthRecordId) {
        jsonData.record_id = currentHealthRecordId;
    }

    // Validate
    if (!jsonData.diagnosis || !jsonData.diagnosis.trim()) {
        alert('Vui lòng nhập chuẩn đoán');
        return;
    }

    // Hiển thị trạng thái loading
    const submitBtn = document.getElementById('saveDiagnosisBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang lưu...';
    submitBtn.disabled = true;

    // Gửi dữ liệu đến server
    fetch('/api/update-diagnosis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(jsonData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Chuẩn đoán đã được lưu thành công!');
            bootstrap.Modal.getInstance(document.getElementById('diagnosisModal')).hide();
            location.reload(); // Reload để cập nhật trạng thái
        } else {
            alert('Lỗi: ' + data.message);
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi lưu chuẩn đoán');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Hàm cập nhật thông tin patient
function updatePatientInfo() {
    const formData = new FormData(document.getElementById('updatePatientForm'));
    const jsonData = Object.fromEntries(formData.entries());

    // Validate
    if (!jsonData.first_name || !jsonData.last_name || !jsonData.phone_number || !jsonData.email) {
        alert('Vui lòng điền đầy đủ thông tin bắt buộc');
        return;
    }

    const updateBtn = document.querySelector('#updatePatientModal .btn-primary');
    const originalText = updateBtn.innerHTML;
    updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang cập nhật...';
    updateBtn.disabled = true;

    // Gửi request đến server
    fetch('/api/update-patient-info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(jsonData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Cập nhật thông tin thành công!');
            bootstrap.Modal.getInstance(document.getElementById('updatePatientModal')).hide();
            location.reload(); // Reload để hiển thị thông tin mới
        } else {
            alert('Lỗi: ' + data.message);
            updateBtn.innerHTML = originalText;
            updateBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi cập nhật thông tin');
        updateBtn.innerHTML = originalText;
        updateBtn.disabled = false;
    });
}