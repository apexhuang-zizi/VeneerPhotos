#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加"下一个"和"汇总下载"功能到 product-processor.html
- 保存后显示两个按钮：下一个、汇总下载
- "下一个"：重置表单，处理下一张
- "汇总下载"：使用 JSZip 打包所有已处理图片
"""

import re

def add_next_and_download(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = content
    
    # 1. 添加 JSZip CDN (在 OpenCV.js 之后)
    jszip_cdn = '\n    <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>'
    
    # 找到 OpenCV.js CDN 的位置
    opencv_pattern = r'(<script src="https://docs\.opencv\.org/4\.8\.0/opencv\.js"></script>)'
    match = re.search(opencv_pattern, modified)
    if match and 'jszip' not in modified.lower():
        insert_pos = match.end()
        modified = modified[:insert_pos] + jszip_cdn + modified[insert_pos:]
        print('✅ 已添加 JSZip CDN')
    else:
        print('⚠️  未找到 OpenCV.js 或 JSZip 已存在')
    
    # 2. 在步骤3的 HTML 中添加"下一个"和"汇总下载"按钮 (隐藏状态)
    step3_actions_pattern = r'(<div class="step-actions" id="step3Actions">)(.*?)(</div>)'
    
    def replace_step3_actions(match):
        prefix = match.group(1)
        content_inner = match.group(2)
        suffix = match.group(3)
        
        # 在保存按钮后面添加两个新按钮 (隐藏)
        new_buttons = '''
          <button class="btn btn-primary" id="btnNext" onclick="nextPhoto()" style="display:none;margin-left:12px;">
            <span>→ 下一个</span>
          </button>
          <button class="btn btn-secondary" id="btnDownloadAll" onclick="downloadAll()" style="display:none;margin-left:12px;">
            <span>📦 汇总下载</span>
          </button>'''
        
        # 在 content_inner 的末尾 (</div> 之前) 插入新按钮
        return prefix + content_inner + new_buttons + '\n        ' + suffix
    
    modified_new = re.sub(step3_actions_pattern, replace_step3_actions, modified, flags=re.DOTALL)
    
    if modified_new == modified:
        print('⚠️  未找到 step3Actions，尝试备用方案')
        # 备用：在步骤3的预览区域添加按钮容器
        step3_preview_pattern = r'(<div class="preview-box" id="previewBox3">.*?)(</div>\s*</div>)'
        def add_button_container(match):
            return match.group(1) + '''
            <div id="afterSaveActions" style="display:none;margin-top:16px;text-align:center;">
              <button class="btn btn-primary" onclick="nextPhoto()">
                <span>→ 下一个</span>
              </button>
              <button class="btn btn-secondary" onclick="downloadAll()" style="margin-left:12px;">
                <span>📦 汇总下载</span>
              </button>
            </div>''' + match.group(2)
        
        modified_new = re.sub(step3_preview_pattern, add_button_container, modified, flags=re.DOTALL)
    
    if modified_new != modified:
        modified = modified_new
        print('✅ 已添加"下一个"和"汇总下载"按钮 (HTML)')
    else:
        print('❌ 无法找到合适的按钮插入位置')
    
    # 3. 修改 showStep 函数，在步骤3时检查是否有已保存的图片，显示按钮
    # 先找到 showStep 函数
    showstep_pattern = r'(function showStep\(step\)\s*\{)(.*?)(^\})'
    
    def modify_showstep(match):
        prefix = match.group(1)
        body = match.group(2)
        
        # 在 showStep 函数末尾 (return 之前) 添加逻辑
        check_logic = '''
  
  // 检查是否显示"下一个"和"汇总下载"按钮
  if (step === 3 && STATE.processedImageBlob) {
    checkSavedImages();
  }
'''
        
        return prefix + body + check_logic
    
    modified_new = re.sub(showstep_pattern, modify_showstep, modified, flags=re.DOTALL | re.MULTILINE)
    
    if modified_new != modified:
        modified = modified_new
        print('✅ 已修改 showStep() 添加按钮显示逻辑')
    else:
        print('⚠️  未找到 showStep 函数')
    
    # 4. 添加 JavaScript 函数：nextPhoto(), downloadAll(), checkSavedImages(), saveToHistory()
    
    new_functions = '''

// ============================================================
// "下一个" 和 "汇总下载" 功能
// ============================================================

// 保存当前图片到历史记录
async function saveToHistory() {
  if (!STATE.processedImageBlob || !STATE.projectId) return;
  
  const record = {
    id: Date.now(),
    projectId: STATE.projectId,
    filename: `processed_${STATE.projectId}_${Date.now()}.png`,
    blob: STATE.processedImageBlob,
    ocrData: { ...STATE.ocrData },
    timestamp: new Date().toISOString()
  };
  
  // 保存到 IndexedDB
  await saveRecordToDB(record);
  
  showToast('✅ 已保存到历史记录');
  console.log('[History] Saved:', record.filename);
}

// 检查是否有已保存的图片，显示按钮
function checkSavedImages() {
  const btnNext = document.getElementById('btnNext');
  const btnDownloadAll = document.getElementById('btnDownloadAll');
  
  if (STATE.processedImageBlob) {
    if (btnNext) btnNext.style.display = 'inline-block';
    if (btnDownloadAll) btnDownloadAll.style.display = 'inline-block';
    console.log('[UI] Show next/ download buttons');
  } else {
    if (btnNext) btnNext.style.display = 'none';
    if (btnDownloadAll) btnDownloadAll.style.display = 'none';
  }
}

// "下一个"：重置表单，处理下一张
function nextPhoto() {
  // 先保存当前图片到历史记录
  saveToHistory();
  
  // 重置 STATE (保留 apiKey, projectId)
  STATE.productImage = null;
  STATE.processedImageBlob = null;
  STATE.barcodeImage = null;
  STATE.ocrData = { a: '', b: '', c: '', d: '' };
  STATE.corners = null;
  STATE.currentStep = 1;
  
  // 清空文件输入
  const fileInput = document.getElementById('fileInput');
  if (fileInput) fileInput.value = '';
  
  // 清空预览
  const preview1 = document.getElementById('preview1');
  if (preview1) preview1.src = '';
  const preview3 = document.getElementById('preview3');
  if (preview3) preview3.src = '';
  
  // 隐藏按钮
  const btnNext = document.getElementById('btnNext');
  const btnDownloadAll = document.getElementById('btnDownloadAll');
  if (btnNext) btnNext.style.display = 'none';
  if (btnDownloadAll) btnDownloadAll.style.display = 'none';
  
  // 回到步骤1
  showStep(1);
  
  showToast('📸 请选择下一张照片');
  console.log('[Next] Reset for next photo');
}

// "汇总下载"：使用 JSZip 打包所有已处理图片
async function downloadAll() {
  if (typeof JSZip === 'undefined') {
    showToast('❌ JSZip 库未加载，无法打包下载');
    console.error('[Download] JSZip not loaded');
    return;
  }
  
  showToast('⏳ 正在打包所有图片...');
  
  try {
    // 从 IndexedDB 加载所有记录
    const records = await loadAllRecordsFromDB(STATE.projectId);
    
    if (!records || records.length === 0) {
      showToast('⚠️ 没有已保存的图片');
      return;
    }
    
    console.log(`[Download] Packing ${records.length} images...`);
    
    const zip = new JSZip();
    const folder = zip.folder(`product_${STATE.projectId}`);
    
    // 添加每个图片到 ZIP
    for (const record of records) {
      const filename = record.filename || `image_${record.id}.png`;
      const blob = record.blob;
      
      if (blob) {
        const arrayBuffer = await blob.arrayBuffer();
        folder.file(filename, arrayBuffer);
        console.log(`[Download] Added: ${filename}`);
      }
    }
    
    // 生成 ZIP 并下载
    const zipBlob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(zipBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `product_${STATE.projectId}_${Date.now()}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast(`✅ 已下载 ${records.length} 张图片 (ZIP)`);
    console.log('[Download] ZIP downloaded successfully');
    
  } catch (err) {
    console.error('[Download] Error:', err);
    showToast('❌ 打包失败: ' + err.message);
  }
}

// 保存记录到 IndexedDB
async function saveRecordToDB(record) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['records'], 'readwrite');
      const store = transaction.objectStore('records');
      
      const putRequest = store.put(record);
      
      putRequest.onsuccess = () => {
        console.log('[IndexedDB] Record saved:', record.filename);
        resolve();
      };
      
      putRequest.onerror = () => {
        console.error('[IndexedDB] Save failed:', putRequest.error);
        reject(putRequest.error);
      };
    };
    
    request.onerror = () => {
      console.error('[IndexedDB] Open failed:', request.error);
      reject(request.error);
    };
  });
}

// 从 IndexedDB 加载所有记录
async function loadAllRecordsFromDB(projectId) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['records'], 'readonly');
      const store = transaction.objectStore('records');
      const index = store.index('projectId');
      
      const getRequest = index.getAll(IDBKeyRange.only(projectId));
      
      getRequest.onsuccess = () => {
        const records = getRequest.result;
        console.log(`[IndexedDB] Loaded ${records.length} records for project ${projectId}`);
        resolve(records);
      };
      
      getRequest.onerror = () => {
        console.error('[IndexedDB] Load failed:', getRequest.error);
        reject(getRequest.error);
      };
    };
    
    request.onerror = () => {
      console.error('[IndexedDB] Open failed:', request.error);
      reject(request.error);
    };
  });
}
'''
    
    # 找到 </script> 标签，在最后一个之前插入新函数
    last_script_pattern = r'(</script>\s*</body>)'
    
    def insert_functions(match):
        return new_functions + '\n\n' + match.group(1)
    
    modified_new = re.sub(last_script_pattern, insert_functions, modified, flags=re.DOTALL)
    
    if modified_new != modified:
        modified = modified_new
        print('✅ 已添加 JavaScript 函数 (nextPhoto, downloadAll, saveToHistory, IndexedDB helpers)')
    else:
        print('⚠️  未找到 </body> 前的 </script>，尝试在文件末尾插入')
        # 备用：直接在 </body> 前插入
        modified = modified.replace('</body>', new_functions + '\n</body>')
        print('✅ 已在 </body> 前插入 JavaScript 函数')
    
    # 5. 修改 processProductImage 函数，在处理完成后自动保存
    # 找到 processProductImage 函数的末尾 (renderStep3 调用之后)
    process_pattern = r'(await renderStep3\(\);)(.*?)(// 处理完成)'
    
    def modify_process(match):
        call_render = match.group(1)
        middle = match.group(2)
        comment = match.group(3)
        
        # 在 renderStep3 之后添加自动保存
        auto_save = '''
  
  // 自动保存到历史记录
  await saveToHistory();
  
  // 显示"下一个"和"汇总下载"按钮
  checkSavedImages();
'''
        
        return call_render + auto_save + middle + comment
    
    modified_new = re.sub(process_pattern, modify_process, modified, flags=re.DOTALL)
    
    if modified_new != modified:
        modified = modified_new
        print('✅ 已修改 processProductImage() 添加自动保存和按钮显示')
    else:
        print('⚠️  未找到 processProductImage 中的 renderStep3 调用')
    
    # 6. 在 IndexedDB 初始化中添加 records object store (如果不存在)
    idb_pattern = r'(const DB_VERSION = 1;)(.*?)(const DB_STORE =)'
    
    def check_idb_version(match):
        prefix = match.group(1)
        middle = match.group(2)
        suffix = match.group(3)
        
        # 修改版本号和 onupgradeneeded 以添加 records store
        new_version = 'const DB_VERSION = 2;'
        
        return new_version + middle + suffix
    
    # 简化：直接查找并替换 DB_VERSION
    modified_new = re.sub(r'const DB_VERSION = 1;', 'const DB_VERSION = 2;', modified)
    
    if modified_new != modified:
        modified = modified_new
        print('✅ 已升级 IndexedDB 版本 (1 → 2)')
    
    # 查找 onupgradeneeded 并添加 records store 创建代码
    upgrade_pattern = r'(request\.onupgradeneeded = \(event\) => \{(.*?)\};)'
    
    def add_records_store(match):
        full_block = match.group(1)
        
        # 检查是否已有 records store 创建代码
        if 'objectStoreNames.contains(' in full_block and 'records' in full_block:
            print('⚠️  IndexedDB 已有 records store')
            return full_block
        
        # 在 onupgradeneeded 中添加 records store 创建
        add_store_code = '''
    
    // 创建 records store (版本 2)
    if (!db.objectStoreNames.contains('records')) {
      const recordStore = db.createObjectStore('records', { keyPath: 'id' });
      recordStore.createIndex('projectId', 'projectId', { unique: false });
      console.log('[IndexedDB] Records store created');
    }
'''
        
        # 在 request.onupgradeneeded 函数体的末尾 (最后一个 } 之前) 插入
        lines = full_block.split('\n')
        # 找到倒数第二个 } (函数体的结束)
        for i in range(len(lines) - 1, -1, -1):
            if '};' in lines[i] or '}' in lines[i]:
                lines.insert(i, add_store_code)
                break
        
        return '\n'.join(lines)
    
    modified_new = re.sub(upgrade_pattern, add_records_store, modified, flags=re.DOTALL)
    
    if modified_new != modified:
        modified = modified_new
        print('✅ 已在 IndexedDB onupgradeneeded 中添加 records store')
    else:
        print('⚠️  未找到 onupgradeneeded (可能已存在 records store)')
    
    # 写回文件
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(modified)
    
    print('\n✅ 修改完成！文件已更新')
    print('📝 新增功能：')
    print('  1. "下一个" 按钮：保存当前图片，重置表单，处理下一张')
    print('  2. "汇总下载" 按钮：使用 JSZip 打包所有已处理图片为 ZIP')
    print('  3. 自动保存：处理完成后自动保存到 IndexedDB')
    print('  4. IndexedDB records store：存储处理历史')

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        html_path = sys.argv[1]
    else:
        html_path = 'product-processor.html'
    
    print(f'🚀 开始修改 {html_path}...\n')
    add_next_and_download(html_path)
    print('\n✅ 完成！请运行语法检查：node -c product-processor.html')
