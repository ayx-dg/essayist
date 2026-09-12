-- gallery.lua — pandoc Lua filter
--
-- Converts groups of images in a single paragraph into a responsive flex gallery.

os.setlocale('C')

local function read_dimensions(src)
  local ok_fetch, mime, contents = pcall(pandoc.mediabag.fetch, src)
  if not ok_fetch then
    io.stderr:write('[gallery] warning: fetch "'
      .. src .. '" failed: ' .. tostring(mime) .. '\n')
    return nil
  end
  if not contents then return nil end

  local ok_size, info = pcall(pandoc.image.size, contents)
  if not ok_size then
    io.stderr:write('[gallery] warning: pandoc.image.size for "'
      .. src .. '" failed: ' .. tostring(info) .. '\n')
    return nil
  end
  if info and info.width and info.height then
    return info.width, info.height
  end
  return nil
end

local function flex_grow(w, h)
  return math.floor(w * 100 / h + 0.5)
end

local function flex_basis(w, h)
  return math.floor(w * 240 / h + 0.5) .. 'px'
end

local function image_to_figure(img)
  local src = img.src
  local alt = pandoc.utils.stringify(img.caption)
  local title = img.title or ''

  local w, h = read_dimensions(src)
  if not w then
    io.stderr:write('[gallery] warning: cannot get dimensions of "'
      .. src .. '", flex layout degraded\n')
  end

  local img_attrs = { loading = 'lazy' }
  if w and h then
    img_attrs.width = tostring(w)
    img_attrs.height = tostring(h)
  end
  local image = pandoc.Image(pandoc.Str(alt), src, title, img_attrs)
  local link = pandoc.Link({ image }, src, '', { target = '_blank' })

  local caption = title ~= '' and title or alt
  local cap = caption ~= '' and pandoc.Caption(pandoc.Str(caption)) or pandoc.Caption{}

  local fig_attrs = { class = 'gallery-image' }
  if w and h then
    fig_attrs.style = string.format('flex-grow:%d;flex-basis:%s', flex_grow(w, h), flex_basis(w, h))
  end

  return pandoc.Figure({ pandoc.Plain({ link }) }, cap, fig_attrs)
end

local pure_image_separators = { Space = true, SoftBreak = true, LineBreak = true }

local function is_pure_image_para(content)
  local count = 0
  for _, item in ipairs(content) do
    if item.t == 'Image' then
      count = count + 1
    elseif not pure_image_separators[item.t] then
      return false
    end
  end
  return count > 0
end

local function build_gallery(images)
  local figures = {}
  for _, img in ipairs(images) do
    figures[#figures + 1] = image_to_figure(img)
  end
  return pandoc.Div(figures, { class = 'gallery' })
end

local GALLERY_CSS = [[
<style>
.gallery { position: relative; display: flex; flex-direction: row; justify-content: center; margin: 1.5em 0; gap: 8px; }
.gallery figure { margin: 0; min-width: 0; }
.gallery a { display: block; }
.gallery img { max-width: 100%; height: auto; display: block; }
.gallery figcaption { text-align: center; font-size: .8em; color: #666; margin-top: .35em; }
</style>
]]

local function is_html_format()
  return FORMAT and FORMAT:match('html')
end

function Para(para)
  if not is_html_format() then return nil end
  if not is_pure_image_para(para.content) then return nil end

  local images = {}
  for _, item in ipairs(para.content) do
    if item.t == 'Image' then images[#images + 1] = item end
  end
  return { build_gallery(images) }
end

function Pandoc(doc)
  if not is_html_format() then return doc end
  doc.blocks:insert(1, pandoc.RawBlock('html', GALLERY_CSS))
  return doc
end

return { Para = Para, Pandoc = Pandoc }
