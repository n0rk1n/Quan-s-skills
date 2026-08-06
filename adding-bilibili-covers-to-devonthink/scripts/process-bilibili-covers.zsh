#!/bin/zsh

set -euo pipefail

readonly SCRIPT_NAME="${0:t}"
# One invocation is one bounded user-visible batch. This is not configurable.
readonly BATCH_LIMIT=50
readonly SOURCE_GROUP_NAME="01 - 无封面图"
readonly DESTINATION_GROUP_NAME="02 - 有封面图"
readonly PARALLEL_DOWNLOADS=4

usage() {
  print -- "Usage:"
  print -- "  $SCRIPT_NAME --root <DEVONthink UUID> [--plan-only]"
  print -- "  $SCRIPT_NAME --plan-manifest <manifest.jsonl>"
  print -- ""
  print -- "Processes at most 50 eligible Bilibili bookmarks per invocation."
}

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    print -u2 -- "Required command not found: $command_name"
    exit 69
  fi
}

select_manifest() {
  local manifest="$1"
  jq -s --argjson limit "$BATCH_LIMIT" '
    [
      .[]
      | select(
          (.uuid | type == "string") and
          (.name | type == "string") and
          (.filename | type == "string") and
          (.coverUrl | type == "string") and
          (.coverUrl | test("^https?://"))
        )
    ][: $limit]
    | {selected_count: length, selected: .}
  ' "$manifest"
}

if (( $# == 1 )) && [[ "$1" == "--help" ]]; then
  usage
  exit 0
fi

if (( $# == 2 )) && [[ "$1" == "--plan-manifest" ]]; then
  require_command jq
  manifest="$2"
  if [[ ! -f "$manifest" ]]; then
    print -u2 -- "Manifest not found: $manifest"
    exit 66
  fi
  select_manifest "$manifest"
  exit 0
fi

plan_only=false
if (( $# == 3 )) && [[ "$1" == "--root" ]] && [[ "$3" == "--plan-only" ]]; then
  root_uuid="$2"
  plan_only=true
elif (( $# == 2 )) && [[ "$1" == "--root" ]]; then
  root_uuid="$2"
else
  usage >&2
  exit 64
fi

if [[ ! "$root_uuid" =~ '^[0-9A-Fa-f-]{36}$' ]]; then
  print -u2 -- "Invalid DEVONthink UUID: $root_uuid"
  exit 65
fi

for command_name in jq osascript; do
  require_command "$command_name"
done

if [[ "$plan_only" == false ]]; then
  for command_name in base64 curl file find mktemp xargs; do
    require_command "$command_name"
  done
fi

run_dir="$(mktemp -d /tmp/devonthink-bilibili-covers.XXXXXX)"
cleanup() {
  rm -rf "$run_dir"
}
trap cleanup EXIT

groups_json="$(osascript -l JavaScript -e "const app=Application(\"com.devon-technologies.think\"); const root=app.getRecordWithUuid(\"$root_uuid\"); if(!root||root.type()!==\"group\") throw new Error(\"目标 UUID 不是 DEVONthink group\"); const children=root.children(); const sources=children.filter(r=>r.type()===\"group\"&&r.name()===\"$SOURCE_GROUP_NAME\"); const destinations=children.filter(r=>r.type()===\"group\"&&r.name()===\"$DESTINATION_GROUP_NAME\"); if(sources.length!==1) throw new Error(\"必须且只能有一个 $SOURCE_GROUP_NAME\"); if(destinations.length!==1) throw new Error(\"必须且只能有一个 $DESTINATION_GROUP_NAME\"); JSON.stringify({root:{uuid:root.uuid(),name:root.name()},source:{uuid:sources[0].uuid(),name:sources[0].name()},destination:{uuid:destinations[0].uuid(),name:destinations[0].name()}})")"

source_uuid="$(jq -r '.source.uuid' <<< "$groups_json")"
destination_uuid="$(jq -r '.destination.uuid' <<< "$groups_json")"
manifest="$run_dir/manifest.jsonl"

# Recognize all historical labels observed in DEVONthink comments.
manifest_json="$(osascript -l JavaScript -e "const app=Application(\"com.devon-technologies.think\"); const src=app.getRecordWithUuid(\"$source_uuid\"); const records=app.search(\"kind:bookmark\",{in:src,excludeSubgroups:true})||[]; const selected=[]; for(const r of records){const comment=r.comment()||\"\"; const match=comment.match(/(?:页面可见封面地址|可见封面 URL|封面 URL)[：:]\\s*(https?:\\/\\/\\S+)/); if(!match) continue; selected.push({uuid:r.uuid(),name:r.name(),filename:r.filename(),coverUrl:match[1]}); if(selected.length===50) break;} JSON.stringify(selected)")"

print -r -- "$manifest_json" | jq -c '.[]' > "$manifest"
plan="$(select_manifest "$manifest")"
selected_count="$(jq -r '.selected_count' <<< "$plan")"

if [[ "$plan_only" == true ]]; then
  jq -n --argjson groups "$groups_json" --argjson plan "$plan" \
    '{batch_limit:50, root:$groups.root, source:$groups.source, destination:$groups.destination, selected_count:$plan.selected_count, selected:$plan.selected}'
  exit 0
fi

if (( selected_count == 0 )); then
  jq -n --argjson groups "$groups_json" \
    '{batch_limit:50, selected_count:0, moved_count:0, failures:[], source:$groups.source, destination:$groups.destination}'
  exit 0
fi

items_dir="$run_dir/items"
mkdir -p "$items_dir"

jq -r '.selected[] | @base64' <<< "$plan" | xargs -P "$PARALLEL_DOWNLOADS" -n 1 /bin/zsh -c '
  set -euo pipefail
  items_dir="$1"
  encoded="$2"
  row=$(print -rn -- "$encoded" | base64 -D)
  uuid=$(jq -r ".uuid" <<< "$row")
  title=$(jq -r ".name" <<< "$row")
  filename=$(jq -r ".filename" <<< "$row")
  cover_url=$(jq -r ".coverUrl" <<< "$row")
  item_dir="$items_dir/$uuid"
  mkdir -p "$item_dir"
  part="$item_dir/download.part"

  # CDN fallback: i0.hdslb.com/i1.hdslb.com use the same resource path.
  request_url="${cover_url/i0.hdslb.com/i1.hdslb.com}"
  if ! curl --fail --location --silent --show-error --retry 2 \
      --connect-timeout 20 --max-time 120 --output "$part" "$request_url"; then
    jq -nc --arg uuid "$uuid" --arg title "$title" --arg url "$cover_url" \
      "{uuid:\$uuid,title:\$title,url:\$url,status:\"download_failed\"}" > "$item_dir/result.json"
    exit 0
  fi

  mime=$(file --brief --mime-type "$part")
  case "$mime" in
    image/webp) extension="webp" ;;
    image/jpeg) extension="jpg" ;;
    image/png) extension="png" ;;
    image/gif) extension="gif" ;;
    *)
      jq -nc --arg uuid "$uuid" --arg title "$title" --arg mime "$mime" \
        "{uuid:\$uuid,title:\$title,mime:\$mime,status:\"invalid_image\"}" > "$item_dir/result.json"
      exit 0
      ;;
  esac

  safe_base="${filename%.*}"
  safe_base="${safe_base//\//-}"
  if [[ -z "$safe_base" ]]; then safe_base="$uuid"; fi
  final_path="$item_dir/$safe_base.$extension"
  mv "$part" "$final_path"
  jq -nc --arg uuid "$uuid" --arg title "$title" --arg path "$final_path" --arg mime "$mime" \
    "{uuid:\$uuid,title:\$title,path:\$path,mime:\$mime,status:\"ok\"}" > "$item_dir/result.json"
' _ "$items_dir"

results="$run_dir/results.jsonl"
find "$items_dir" -name result.json -print0 | xargs -0 jq -c '.' > "$results"
successes="$run_dir/successes.json"
jq -s '[.[] | select(.status=="ok")]' "$results" > "$successes"
download_failures="$(jq -s '[.[] | select(.status!="ok")]' "$results")"

apply_out="$(osascript -l JavaScript -e "ObjC.import(\"Foundation\"); const text=ObjC.unwrap(\$.NSString.stringWithContentsOfFileEncodingError(\$(\"$successes\"),\$.NSUTF8StringEncoding,null)); const rows=JSON.parse(text); const app=Application(\"com.devon-technologies.think\"); const src=app.getRecordWithUuid(\"$source_uuid\"); const dst=app.getRecordWithUuid(\"$destination_uuid\"); const ok=[],errors=[]; for(const row of rows){let stage=\"lookup\"; try{const bm=app.getRecordWithUuid(row.uuid); if(!bm||bm.type()!==\"bookmark\") throw new Error(\"找不到源书签\"); const title=bm.name(); const prior=(app.search(row.uuid,{in:dst,excludeSubgroups:true})||[]).find(r=>r.type()===\"picture\"&&(r.comment()||\"\").includes(\"封面来源书签 UUID：\"+row.uuid)); let pic=prior; if(!pic){stage=\"import\"; pic=app.importPath(row.path,{to:dst}); if(!pic) throw new Error(\"封面导入失败\"); pic.comment=\"封面来源书签 UUID：\"+row.uuid;} pic.name=title; stage=\"move\"; const moved=app.move({record:bm,from:src,to:dst}); if(!moved) throw new Error(\"书签移动失败\"); ok.push({uuid:row.uuid,title,pictureUuid:pic.uuid()});}catch(e){errors.push({uuid:row.uuid,stage,error:String(e)});}} JSON.stringify({succeeded:ok.length,failed:errors.length,ok,errors})")"

source_remaining="$(osascript -l JavaScript -e "const app=Application(\"com.devon-technologies.think\"); const src=app.getRecordWithUuid(\"$source_uuid\"); app.search(\"kind:bookmark\",{in:src,excludeSubgroups:true}).length")"
destination_bookmarks="$(osascript -l JavaScript -e "const app=Application(\"com.devon-technologies.think\"); const dst=app.getRecordWithUuid(\"$destination_uuid\"); app.search(\"kind:bookmark\",{in:dst,excludeSubgroups:true}).length")"
destination_pictures="$(osascript -l JavaScript -e "const app=Application(\"com.devon-technologies.think\"); const dst=app.getRecordWithUuid(\"$destination_uuid\"); app.search(\"kind:picture\",{in:dst,excludeSubgroups:true}).length")"

jq -n \
  --argjson groups "$groups_json" \
  --argjson selected "$selected_count" \
  --argjson download_failures "$download_failures" \
  --argjson applied "$apply_out" \
  --argjson source_remaining "$source_remaining" \
  --argjson destination_bookmarks "$destination_bookmarks" \
  --argjson destination_pictures "$destination_pictures" \
  '{
    batch_limit:50,
    selected_count:$selected,
    moved_count:$applied.succeeded,
    failed_count:($download_failures|length)+$applied.failed,
    failures:($download_failures+$applied.errors),
    source_remaining:$source_remaining,
    destination_bookmarks:$destination_bookmarks,
    destination_pictures:$destination_pictures,
    source:$groups.source,
    destination:$groups.destination
  }'
