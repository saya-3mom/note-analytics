const files = [
  "../articles.csv",
  "../observations.csv"
];

async function csv(path){
  const r = await fetch(path);

  if(!r.ok){
    throw new Error(path + " を読み込めません");
  }

  return parse(await r.text());
}


function parse(text){
  const rows = [];
  let row = [];
  let cell = "";
  let q = false;

  for(let i=0; i<text.length; i++){
    const c = text[i];

    if(c === '"'){
      if(q && text[i + 1] === '"'){
        cell += '"';
        i++;
      }else{
        q = !q;
      }

    }else if(c === "," && !q){
      row.push(cell);
      cell = "";

    }else if((c === "\n" || c === "\r") && !q){

      if(c === "\r" && text[i + 1] === "\n"){
        i++;
      }

      row.push(cell);

      if(row.some(x => x !== "")){
        rows.push(row);
      }

      row = [];
      cell = "";

    }else{
      cell += c;
    }
  }

  if(cell || row.length){
    row.push(cell);

    if(row.some(x => x !== "")){
      rows.push(row);
    }
  }

  if(!rows.length){
    return [];
  }

  const h = rows[0].map(
    x => x.replace(/^\ufeff/, "")
  );

  return rows.slice(1).map(r =>
    Object.fromEntries(
      h.map((x,i) => [x, r[i] ?? ""])
    )
  );
}


const n = x => Number(x || 0);

const fmt = x =>
  n(x).toLocaleString("ja-JP");

const esc = x =>
  String(x ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;");


/*
 * 日本時間の日付だけを取り出す
 */
function japanDate(value){

  const d = new Date(value);

  return new Intl.DateTimeFormat(
    "sv-SE",
    {
      timeZone:"Asia/Tokyo",
      year:"numeric",
      month:"2-digit",
      day:"2-digit"
    }
  ).format(d);
}


/*
 * 公開日から観測日までの日数
 *
 * 公開当日 = 0日目
 * 翌日     = 1日目
 * 2日後    = 2日目
 */
function daysAfterPublished(publishedAt, observedAt){

  const published = japanDate(publishedAt);
  const observed = japanDate(observedAt + "T00:00:00+09:00");

  const p = new Date(published + "T00:00:00+09:00");
  const o = new Date(observed + "T00:00:00+09:00");

  return Math.round(
    (o - p) / (1000 * 60 * 60 * 24)
  );
}


/*
 * 記事ごとの観測データを
 * note_keyでまとめる
 *
 * management_idでは紐付けない。
 */
function groupObservations(obs){

  const groups = {};

  obs.forEach(o => {

    if(!o.note_key){
      return;
    }

    (groups[o.note_key] ??= []).push(o);
  });

  Object.values(groups).forEach(rows => {
    rows.sort(
      (a,b) =>
        a.observed_at.localeCompare(b.observed_at)
    );
  });

  return groups;
}


/*
 * 記事マスタと観測データを合体
 */
function buildArticles(articles, obs){

  const groups = groupObservations(obs);

  return articles
    .filter(a => a.management_id && a.note_key)
    .map(a => {

      const rows = groups[a.note_key] || [];

      if(!rows.length){
        return null;
      }

      const latest = rows.at(-1);
      const previous =
        rows.length > 1
          ? rows.at(-2)
          : null;

      const views = n(latest.views);
      const likes = n(latest.likes);
      const comments = n(latest.comments);

      const diff =
        previous
          ? views - n(previous.views)
          : null;

      const rate =
        views
          ? likes / views * 100
          : 0;

      /*
       * さらにひとつ前の増加量
       *
       * 例：
       * 前々回 → 前回 +1
       * 前回   → 今回 +5
       *
       * acceleration = +4
       */
      let previousDiff = null;

      if(rows.length >= 3){

        const before = rows.at(-3);

        previousDiff =
          n(previous.views) -
          n(before.views);
      }

      const acceleration =
        previousDiff !== null && diff !== null
          ? diff - previousDiff
          : null;

      return {
        ...a,

        views,
        likes,
        comments,

        diff,
        previousDiff,
        acceleration,

        observed: latest.observed_at,
        rate,

        rows
      };

    })
    .filter(Boolean);
}


/*
 * サマリー
 */
function renderSummary(latest){

  const total =
    latest.reduce(
      (s,a) => s + a.views,
      0
    );

  const diff =
    latest.reduce(
      (s,a) => s + (a.diff ?? 0),
      0
    );

  const rate =
    latest.length
      ? latest.reduce(
          (s,a) => s + a.rate,
          0
        ) / latest.length
      : 0;

  document.querySelector("#count")
    .textContent = latest.length;

  document.querySelector("#views")
    .textContent = fmt(total);

  document.querySelector("#diff")
    .textContent =
      (diff >= 0 ? "+" : "") +
      fmt(diff);

  document.querySelector("#rate")
    .textContent =
      rate.toFixed(1) + "%";

  const dates =
    latest
      .map(a => a.observed)
      .filter(Boolean)
      .sort();

  document.querySelector("#updated")
    .textContent =
      dates.length
        ? "最終観測：" + dates.at(-1)
        : "最終観測：-";
}


/*
 * 記事一覧
 */
function renderArticles(latest){

  const sorted =
    [...latest]
      .sort((a,b) => b.views - a.views);

  document.querySelector("#table")
    .innerHTML =
      sorted.map(a => `
        <tr>

          <td>
            ${esc(a.management_id)}
          </td>

          <td title="${esc(a.title)}">
            <a
              href="${esc(a.url)}"
              target="_blank"
              rel="noopener noreferrer"
            >
              ${esc(a.title)}
            </a>
          </td>

          <td>
            ${fmt(a.views)}
          </td>

          <td class="${a.diff > 0 ? "up" : ""}">
            ${
              a.diff === null
                ? "—"
                : (a.diff >= 0 ? "+" : "") +
                  fmt(a.diff)
            }
          </td>

          <td>
            ${fmt(a.likes)}
          </td>

          <td>
            ${a.rate.toFixed(1)}%
          </td>

          <td>
            ${fmt(a.comments)}
          </td>

        </tr>
      `)
      .join("");
}


/*
 * 公開後の初速
 *
 * 直近の記事を中心に、
 * 公開後1〜7日目の観測を表示。
 */
function renderSpeed(latest){

  const rows = latest
    .map(a => {

      const speed = {
        1: null,
        3: null,
        7: null
      };

      a.rows.forEach(o => {

        const day =
          daysAfterPublished(
            a.published_at,
            o.observed_at
          );

        if(day === 1 || day === 3 || day === 7){
          speed[day] = n(o.views);
        }

      });

      return {
        article: a,
        speed
      };

    })
    // 1日後のデータがある記事だけ表示
    .filter(x => x.speed[1] !== null)
    // 1日後のビュー数が多い順
    .sort((a,b) =>
      b.speed[1] - a.speed[1]
    );


  document.querySelector("#speedTable")
    .innerHTML =
      rows.length
        ? rows.map(x => `
            <tr>

              <td title="${esc(x.article.title)}">
                <a
                  href="${esc(x.article.url)}"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  ${esc(x.article.title)}
                </a>
              </td>

              <td>
                ${esc(x.article.genre || "未分類")}
              </td>

              <td>
                ${x.speed[1] === null
                  ? "—"
                  : fmt(x.speed[1])}
              </td>

              <td>
                ${x.speed[3] === null
                  ? "—"
                  : fmt(x.speed[3])}
              </td>

              <td>
                ${x.speed[7] === null
                  ? "—"
                  : fmt(x.speed[7])}
              </td>

            </tr>
          `).join("")
        : `
          <tr>
            <td colspan="5" class="empty">
              1日後の観測データがまだありません。
            </td>
          </tr>
        `;
}


/*
 * ジャンル別平均
 */
function renderGenres(latest){

  const groups = {};

  latest.forEach(a => {

    const genre =
      a.genre || "未分類";

    (groups[genre] ??= []).push(a);

  });


  const rows =
    Object.entries(groups)
      .map(([genre,articles]) => {

        const avgViews =
          articles.reduce(
            (s,a) => s + a.views,
            0
          ) / articles.length;

        const avgLikes =
          articles.reduce(
            (s,a) => s + a.likes,
            0
          ) / articles.length;

        const avgRate =
          articles.reduce(
            (s,a) => s + a.rate,
            0
          ) / articles.length;

        return {
          genre,
          count:articles.length,
          avgViews,
          avgLikes,
          avgRate
        };

      })
      .sort(
        (a,b) =>
          b.avgViews - a.avgViews
      );


  document.querySelector("#genreTable")
    .innerHTML =
      rows.map(x => `
        <tr>

          <td>
            ${esc(x.genre)}
          </td>

          <td>
            ${x.count}
          </td>

          <td>
            ${Math.round(x.avgViews).toLocaleString("ja-JP")}
          </td>

          <td>
            ${x.avgLikes.toFixed(1)}
          </td>

          <td>
            ${x.avgRate.toFixed(1)}%
          </td>

        </tr>
      `)
      .join("");
}


/*
 * 最近伸び始めた記事
 *
 * 「前回比」がさらに大きくなった記事を
 * accelerationとして評価。
 */
function renderGrowth(latest){

  const ranking =
    [...latest]
      .filter(
        a =>
          a.acceleration !== null &&
          a.acceleration > 0
      )
      .sort(
        (a,b) =>
          b.acceleration -
          a.acceleration
      )
      .slice(0,5);


  document.querySelector("#growth")
    .innerHTML =
      ranking.length
        ? ranking.map((a,i) => `

            <div class="growth-item">

              <div class="growth-no">
                ${i + 1}
              </div>

              <div class="growth-id">
                ${esc(a.management_id)}
              </div>

              <div
                class="growth-title"
                title="${esc(a.title)}"
              >
                <a
                  href="${esc(a.url)}"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  ${esc(a.title)}
                </a>
              </div>

              <div class="growth-diff">
                ${
                  a.diff >= 0
                    ? "+"
                    : ""
                }${fmt(a.diff)} views
              </div>

              <div class="growth-accel">
                前回より
                ${
                  a.acceleration >= 0
                    ? "+"
                    : ""
                }${fmt(a.acceleration)}
              </div>

            </div>

          `).join("")
        : `
          <div class="empty">
            伸びが加速している記事はまだありません。
          </div>
        `;
}


/*
 * メイン
 */
async function main(){

  const [articles, obs] =
    await Promise.all(
      files.map(csv)
    );


  const latest =
    buildArticles(
      articles,
      obs
    );


  renderSummary(latest);
  renderArticles(latest);
  renderSpeed(latest);
  renderGenres(latest);
  renderGrowth(latest);
}


main().catch(e => {

  document.querySelector("main").innerHTML = `
    <section class="card">

      <h2>読み込みエラー</h2>

      <p>
        ${esc(e.message)}
      </p>

      <p>
        articles.csv と observations.csv
        を読み込める場所に置いてください。
      </p>

    </section>
  `;

});