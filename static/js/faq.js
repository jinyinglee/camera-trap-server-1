let content_dict = {'web':{'title': '網頁操作','content':`
<div class="accordion" id="accordionExample">
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingOne">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
      網頁操作說明文件
      </button>
    </h2>
    <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="headingOne" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <a class="link" target="_blank" href="/media/faq/網頁版系統操作.pdf">點此下載</a>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading2">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse2" aria-expanded="false" aria-controls="collapse2">
      網頁操作說明影片
      </button>
    </h2>
    <div id="collapse2" class="accordion-collapse collapse" aria-labelledby="heading2" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <video class="img lazy mx-auto d-block" controls width="100%" preload="none">
          <source src="/media/faq/網頁版系統操作影片.mp4" type="video/mp4">
          抱歉，您的瀏覽器不支援內嵌影片。
        </video>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading3">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse3" aria-expanded="false" aria-controls="collapse3">
      計畫承辦人及計畫總管理人的差異？
      </button>
    </h2>
    <div id="collapse3" class="accordion-collapse collapse" aria-labelledby="heading3" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>計畫承辦人為單一計畫的管理者。計畫總管理人為單位管理者，可管理所屬單位的所有計畫。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading4">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse4" aria-expanded="false" aria-controls="collapse4">
      我看不到所屬的計畫，可以怎麼處理？
      </button>
    </h2>
    <div id="collapse4" class="accordion-collapse collapse" aria-labelledby="heading4" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>請聯繫計畫承辦人或計畫總管理人協助將您加入計畫成員。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading5">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse5" aria-expanded="false" aria-controls="collapse5">
      相機樣點運作及缺失比例中的缺失原因要由誰填寫？
      </button>
    </h2>
    <div id="collapse5" class="accordion-collapse collapse" aria-labelledby="heading5" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>登入後的所有帳號皆可填寫，由計畫承辦人決定是要自行填寫、或請資料上傳者填寫皆可。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading6">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse6" aria-expanded="false" aria-controls="collapse6">
      我下載的excel檔案是亂碼，可以怎麼處理？
      </button>
    </h2>
    <div id="collapse6" class="accordion-collapse collapse" aria-labelledby="heading6" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>打開excel，點選上方的「資料」後，選擇「取得外部資料」並選取您欲打開的excel檔案，於檔案來源下拉選單中選擇包含UTF-8的選項，並以逗號分隔，應可排除亂碼問題。</p>
      </div>
    </div>
  </div>
</div>
`},

'account': { 'title': '帳號相關', 'content': `
<div class="accordion" id="accordionExample">
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingOne">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
        有哪幾種登入方式？
      </button>
    </h2>
    <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="headingOne" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      本平台目前僅能透過 ORCiD 帳號進行登入，若尚未註冊請先至 ORCiD 官網 (<a class="link" href="https://orcid.org/" target="_blank">https://orcid.org/</a>) 申請帳號，網站預設為英文版，可自行調整語系。<br/> ORCiD 可使用 Google 或 Facebook 認證。      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingTwo">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
        為何無法順利登入？
      </button>
    </h2>
    <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="headingTwo" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <p>可能原因：<br/> 瀏覽器不支援，請使用Google Chrome 或 Firefox。<br/> 瀏覽器版本未更新至最新版。</p>
      </div>
    </div>
  </div>
</div>
`},

'project': {'title': '計畫管理','content': `
<div class="accordion" id="accordionExample">
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingOne">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
      新增計畫需要填寫哪些基本資訊？
      </button>
    </h2>
    <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="headingOne" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      下列為必填之選項，可於新增計畫前先行檢視：
      <ul>
      <li>計畫名稱</li>
      <li>計畫主持人</li>
      <li>計畫執行時間</li>
      <li>創用CC授權許可（分別針對詮釋資料、鑑定資訊、影像資料作授權，了解<a href="http://creativecommons.tw/" class="link" target="_blank">創用 CC 授權內容</a>）</li>
      <li>計畫資料公開日期</li>
      </ul>      
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingTwo">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
        為何需要填寫計畫簡稱？
      </button>
    </h2>
    <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="headingTwo" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <p>由於計畫名稱可能較長、且部分計畫可能為多年期計畫，為使後續資料搜尋或運算有一致性，可改使用計畫簡稱來辨別特定計畫。計畫簡稱非必填選項。</p>
      </div>
    </div>
  </div>
</div>
`},

'desktop': {'title': '單機版軟體操作','content': `
<div class="accordion" id="accordionExample">
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingOne">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
      軟體操作說明文件
      </button>
    </h2>
    <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="headingOne" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <a class="link" target="_blank" href="/media/faq/單機版系統操作.pdf">點此下載</a>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingTwo">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
      軟體操作說明影片
      </button>
    </h2>
    <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="headingTwo" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <video class="img lazy mx-auto d-block" controls width="100%" preload="none">
          <source src="/media/faq/單機版系統操作影片.mp4" type="video/mp4">
            抱歉，您的瀏覽器不支援內嵌影片。
        </video>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingThree">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
      有沒有建議的資料夾命名邏輯？
      </button>
    </h2>
    <div id="collapseThree" class="accordion-collapse collapse" aria-labelledby="headingThree" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>資料夾命名需有固定格式：<b>名稱-行程開始日期-行程結束日期</b>，否則會跳出警告視窗、無法匯入。其中名稱可自訂，日期則各自需為 yyyymmdd 八碼數字，中間皆需有「-」符號。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading4">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse4" aria-expanded="false" aria-controls="collapse4">
      一個資料夾有沒有影像數量或大小上限？
      </button>
    </h2>
    <div id="collapse4" class="accordion-collapse collapse" aria-labelledby="heading4" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>沒有數量或大小上限。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading5">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse5" aria-expanded="false" aria-controls="collapse5">
      是否可以新增資料欄位？
      </button>
    </h2>
    <div id="collapse5" class="accordion-collapse collapse" aria-labelledby="heading5" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>目前未開放自行新增欄位。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading6">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse6" aria-expanded="false" aria-controls="collapse6">
      上傳至系統的影像檔是原檔嗎？
      </button>
    </h2>
    <div id="collapse6" class="accordion-collapse collapse" aria-labelledby="heading6" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>系統儲存的為壓縮後之檔案，解析度在一般狀況下使用無問題，但如特定影像有放大圖需求，建議自行保留一份原檔。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading7">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse7" aria-expanded="false" aria-controls="collapse7">
      上傳容量大小有限制嗎？
      </button>
    </h2>
    <div id="collapse7" class="accordion-collapse collapse" aria-labelledby="heading7" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>上傳容量大小沒有限制，但如果容量太大建議可以分成不同資料夾上傳，避免單一資料夾上傳太久。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading8">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse8" aria-expanded="false" aria-controls="collapse8">
      影片可以上傳嗎？
      </button>
    </h2>
    <div id="collapse8" class="accordion-collapse collapse" aria-labelledby="heading8" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>影片可以上傳。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading9">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse9" aria-expanded="false" aria-controls="collapse9">
      影像上傳中斷的話會需要整個資料夾重新上傳嗎？
      </button>
    </h2>
    <div id="collapse9" class="accordion-collapse collapse" aria-labelledby="heading9" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>若上傳中斷，可重新開啟軟體，於上傳頁面點選「重啟上傳」鍵，即會從上次中斷處繼續上傳。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading10">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse10" aria-expanded="false" aria-controls="collapse10">
      此軟體使用時會需要在有網路的環境嗎？
      </button>
    </h2>
    <div id="collapse10" class="accordion-collapse collapse" aria-labelledby="heading10" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>僅有在<b>選取計畫、樣區、相機位置</b>，以及<b>影像上傳</b>時，會需要在有網路的環境，其餘的匯入與編輯動作不需要有網路才能使用。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading11">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse11" aria-expanded="false" aria-controls="collapse11">
      我有連上網路，但還是無法上傳？
      </button>
    </h2>
    <div id="collapse11" class="accordion-collapse collapse" aria-labelledby="heading11" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>有可能是您單位所在網域阻擋本軟體使用，請改使用自己的個人網路，如還是無法上傳，請填寫意見回饋或聯繫維運團隊。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading12">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse12" aria-expanded="false" aria-controls="collapse12">
      如果無法一次整理完照片，可以先暫存之後再繼續處理嗎？
      </button>
    </h2>
    <div id="collapse12" class="accordion-collapse collapse" aria-labelledby="heading12" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>可以，欄位只要有成功輸入內容，即表示已存檔，即使關閉檔案，下次重開仍會保留前一次的編輯內容。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading13">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse13" aria-expanded="false" aria-controls="collapse13">
      影像上傳與資料編輯兩者只能在同一台電腦進行嗎？
      </button>
    </h2>
    <div id="collapse13" class="accordion-collapse collapse" aria-labelledby="heading13" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>若希望換一台電腦繼續編輯或上傳，可直接將編輯後的整個目錄檔案搬移到另一台電腦，即可轉移使用。目錄檔案包含 app.exe / config.ini / ct.db / ct-log.txt / thumbnails。</p>
      </div>
    </div>
  </div>
  <div class="accordion-item">
    <h2 class="accordion-header" id="heading14">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse14" aria-expanded="false" aria-controls="collapse14">
      影像上傳後是否還能夠修正？
      </button>
    </h2>
    <div id="collapse14" class="accordion-collapse collapse" aria-labelledby="heading14" data-bs-parent="#accordionExample">
      <div class="accordion-body">
      <p>如為文字調整，可直接在軟體上更新並覆蓋舊文字資料；若為影像有問題（如重複上傳相同影像、或影像上傳至錯誤之相機位置），則請聯繫計畫承辦人或計畫總管理人協助調整。</p>
      </div>
    </div>
  </div>
</div>
`}




}

$(document).ready($(".faq-content").html(content_dict["web"]["content"]));

$(".nl").on("click", function () {
  $(".nl").removeClass("active");
  $(this).addClass("active");
  let type = $(this).data("type");
  $(".faq-title").html(content_dict[type]["title"]);
  $(".faq-content").html(content_dict[type]["content"]);
});