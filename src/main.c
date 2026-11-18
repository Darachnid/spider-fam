#include <pebble.h>
#include <string.h>

#define PERSIST_KEY_COLOR_SPIDER 1
#define PERSIST_KEY_DARK_BACKGROUND 2
#define PERSIST_KEY_PREVIEW_SPECIES 3
#define PREVIEW_INTERVAL_MS 3000
#define PLATE_LOAD_RETRY_MS 150
#define PLATE_LOAD_MAX_RETRIES 12

typedef struct {
  uint32_t color_resource_id;
  uint32_t mono_resource_id;
  const char *common;
  const char *scientific;
} Spider;

#include "spider_table.inc"

static Window *s_window;
static BitmapLayer *s_spider_layer;
static TextLayer *s_time_layer, *s_date_layer, *s_common_layer, *s_scientific_layer;
static GBitmap *s_spider_bitmap;
static int32_t s_day = -1;
static int s_spider_index = -1;
static bool s_color_spider = true;
static bool s_dark_background = false;
static bool s_preview_species = false;
static AppTimer *s_preview_timer;
static AppTimer *s_load_retry_timer;
static int s_load_retry_count;
static char s_time_buffer[16], s_date_buffer[24];

static void display_spider(int index);
static int daily_spider(int32_t day);
static void show_plate_for_mode(void);

static GColor text_color(void) {
  return s_dark_background ? GColorWhite : GColorBlack;
}

static GColor background_color(void) {
  return s_dark_background ? GColorBlack : GColorWhite;
}

static void apply_theme(void) {
  window_set_background_color(s_window, background_color());
  bitmap_layer_set_background_color(s_spider_layer, background_color());
  text_layer_set_text_color(s_time_layer, text_color());
  text_layer_set_text_color(s_date_layer, text_color());
  text_layer_set_text_color(s_common_layer, text_color());
  text_layer_set_text_color(s_scientific_layer, text_color());
}

static uint32_t spider_resource_id(int index) {
  if (index < 0 || index >= NUM_SPIDER) {
    return 0;
  }
  return s_color_spider ? SPIDER[index].color_resource_id : SPIDER[index].mono_resource_id;
}

static void preview_timer_callback(void *context) {
  if (!s_preview_species) {
    s_preview_timer = NULL;
    return;
  }
  int next = s_spider_index < 0 ? 0 : (s_spider_index + 1) % NUM_SPIDER;
  display_spider(next);
  s_preview_timer = app_timer_register(PREVIEW_INTERVAL_MS, preview_timer_callback, NULL);
}

static void update_preview_timer(void) {
  if (s_preview_timer) {
    app_timer_cancel(s_preview_timer);
    s_preview_timer = NULL;
  }
  if (!s_preview_species) {
    show_plate_for_mode();
    return;
  }
  s_preview_timer = app_timer_register(PREVIEW_INTERVAL_MS, preview_timer_callback, NULL);
}

static void set_preview_species(bool enabled) {
  if (enabled == s_preview_species) {
    return;
  }
  s_preview_species = enabled;
  persist_write_bool(PERSIST_KEY_PREVIEW_SPECIES, s_preview_species);
  update_preview_timer();
}

static int32_t absolute_day(const struct tm *t) {
  int32_t year = t->tm_year + 1900;
  int32_t y = year - 1;
  return 365 * y + y / 4 - y / 100 + y / 400 + t->tm_yday;
}

static int daily_spider(int32_t day) {
  return (int)(((uint32_t)day * 17u + 31u) % NUM_SPIDER);
}

static GBitmap *load_plate_bitmap(int index) {
  uint32_t primary = spider_resource_id(index);
  uint32_t alternate = s_color_spider ? SPIDER[index].mono_resource_id
                                      : SPIDER[index].color_resource_id;
  GBitmap *bitmap = gbitmap_create_with_resource(primary);
  if (!bitmap && alternate != primary) {
    bitmap = gbitmap_create_with_resource(alternate);
  }
  return bitmap;
}

static void cancel_load_retry(void) {
  if (s_load_retry_timer) {
    app_timer_cancel(s_load_retry_timer);
    s_load_retry_timer = NULL;
  }
}

static void load_retry_callback(void *context) {
  int index = (int)(intptr_t)context;
  s_load_retry_timer = NULL;
  if (index < 0 || index >= NUM_SPIDER || index != s_spider_index) {
    return;
  }
  GBitmap *replacement = load_plate_bitmap(index);
  if (!replacement) {
    if (s_load_retry_count < PLATE_LOAD_MAX_RETRIES) {
      s_load_retry_count++;
      s_load_retry_timer = app_timer_register(PLATE_LOAD_RETRY_MS, load_retry_callback,
                                            (void *)(intptr_t)index);
    }
    return;
  }
  s_load_retry_count = 0;
  bitmap_layer_set_bitmap(s_spider_layer, NULL);
  if (s_spider_bitmap) {
    gbitmap_destroy(s_spider_bitmap);
  }
  s_spider_bitmap = replacement;
  bitmap_layer_set_bitmap(s_spider_layer, s_spider_bitmap);
}

static void display_spider(int index) {
  if (index < 0 || index >= NUM_SPIDER) {
    return;
  }
  text_layer_set_text(s_common_layer, SPIDER[index].common);
  text_layer_set_text(s_scientific_layer, SPIDER[index].scientific);
  s_spider_index = index;
  cancel_load_retry();
  s_load_retry_count = 0;
  load_retry_callback((void *)(intptr_t)index);
}

static void show_plate_for_mode(void) {
  int index;
  if (s_preview_species) {
    index = (s_spider_index >= 0) ? s_spider_index : 0;
  } else if (s_day >= 0) {
    index = daily_spider(s_day);
  } else {
    time_t now = time(NULL);
    index = daily_spider(absolute_day(localtime(&now)));
  }
  display_spider(index);
}

static void update_display(struct tm *tick) {
  int32_t day = absolute_day(tick);
  if (day != s_day) {
    s_day = day;
    if (!s_preview_species) {
      display_spider(daily_spider(day));
    }
  }
  strftime(s_time_buffer, sizeof(s_time_buffer),
           clock_is_24h_style() ? "%H:%M" : "%I:%M", tick);
  if (!clock_is_24h_style() && s_time_buffer[0] == '0') {
    memmove(s_time_buffer, s_time_buffer + 1, strlen(s_time_buffer));
  }
  strftime(s_date_buffer, sizeof(s_date_buffer), "%a, %b %e", tick);
  text_layer_set_text(s_time_layer, s_time_buffer);
  text_layer_set_text(s_date_layer, s_date_buffer);
}

static void tick_handler(struct tm *tick, TimeUnits changed) {
  update_display(tick);
}

static void load_persisted_settings(void) {
  if (persist_exists(PERSIST_KEY_COLOR_SPIDER)) {
    s_color_spider = persist_read_bool(PERSIST_KEY_COLOR_SPIDER);
  }
  if (persist_exists(PERSIST_KEY_DARK_BACKGROUND)) {
    s_dark_background = persist_read_bool(PERSIST_KEY_DARK_BACKGROUND);
  }
}

static void inbox_received_callback(DictionaryIterator *iterator, void *context) {
  bool style_changed = false;
  bool theme_changed = false;

  Tuple *color_tuple = dict_find(iterator, MESSAGE_KEY_ColorSpider);
  if (color_tuple) {
    bool next = color_tuple->value->uint8 != 0;
    if (next != s_color_spider) {
      s_color_spider = next;
      persist_write_bool(PERSIST_KEY_COLOR_SPIDER, s_color_spider);
      style_changed = true;
    }
  }

  Tuple *preview_tuple = dict_find(iterator, MESSAGE_KEY_PreviewCycle);
  if (preview_tuple) {
    set_preview_species(preview_tuple->value->uint8 != 0);
  }

  Tuple *bg_tuple = dict_find(iterator, MESSAGE_KEY_DarkBackground);
  if (bg_tuple) {
    bool next = false;
    if (bg_tuple->type == TUPLE_CSTRING) {
      next = strcmp(bg_tuple->value->cstring, "1") == 0;
    } else {
      next = bg_tuple->value->uint8 != 0;
    }
    if (next != s_dark_background) {
      s_dark_background = next;
      persist_write_bool(PERSIST_KEY_DARK_BACKGROUND, s_dark_background);
      theme_changed = true;
    }
  }

  if (theme_changed) {
    apply_theme();
  }
  if (style_changed && s_spider_index >= 0) {
    display_spider(s_spider_index);
  }
}

static TextLayer *make_label(GRect frame, const char *font_key, GTextAlignment align) {
  TextLayer *layer = text_layer_create(frame);
  text_layer_set_background_color(layer, GColorClear);
  text_layer_set_text_color(layer, text_color());
  text_layer_set_font(layer, fonts_get_system_font(font_key));
  text_layer_set_text_alignment(layer, align);
  layer_add_child(window_get_root_layer(s_window), text_layer_get_layer(layer));
  return layer;
}

static void init(void) {
  load_persisted_settings();

  s_window = window_create();
  window_set_background_color(s_window, background_color());
  window_stack_push(s_window, true);

  Layer *root = window_get_root_layer(s_window);
  GRect bounds = layer_get_bounds(root);
  int w = bounds.size.w;

  s_spider_layer = bitmap_layer_create(GRect(6, 15, w - 12, 106));
  bitmap_layer_set_alignment(s_spider_layer, GAlignCenter);
  bitmap_layer_set_background_color(s_spider_layer, background_color());
  bitmap_layer_set_compositing_mode(s_spider_layer, GCompOpAssign);
  layer_add_child(root, bitmap_layer_get_layer(s_spider_layer));

  s_common_layer = make_label(GRect(4, 125, w - 8, 22), FONT_KEY_GOTHIC_18_BOLD, GTextAlignmentCenter);
  s_scientific_layer = make_label(GRect(4, 147, w - 8, 22), FONT_KEY_GOTHIC_14, GTextAlignmentCenter);
  s_time_layer = make_label(GRect(2, 171, w - 4, 45), FONT_KEY_BITHAM_42_BOLD, GTextAlignmentCenter);
  s_date_layer = make_label(GRect(4, 210, w - 8, 18), FONT_KEY_GOTHIC_14, GTextAlignmentCenter);

  app_message_register_inbox_received(inbox_received_callback);
  app_message_open(64, 64);

  if (persist_exists(PERSIST_KEY_PREVIEW_SPECIES)) {
    s_preview_species = persist_read_bool(PERSIST_KEY_PREVIEW_SPECIES);
  } else {
    s_preview_species = false;
  }

  time_t now = time(NULL);
  struct tm *tick = localtime(&now);
  update_display(tick);
  if (s_spider_index < 0) {
    show_plate_for_mode();
  }
  if (s_preview_species) {
    update_preview_timer();
  }
  tick_timer_service_subscribe(MINUTE_UNIT, tick_handler);
}

static void deinit(void) {
  if (s_preview_timer) {
    app_timer_cancel(s_preview_timer);
    s_preview_timer = NULL;
  }
  cancel_load_retry();
  tick_timer_service_unsubscribe();
  app_message_deregister_callbacks();
  if (s_spider_bitmap) {
    gbitmap_destroy(s_spider_bitmap);
  }
  bitmap_layer_destroy(s_spider_layer);
  text_layer_destroy(s_time_layer);
  text_layer_destroy(s_date_layer);
  text_layer_destroy(s_common_layer);
  text_layer_destroy(s_scientific_layer);
  window_destroy(s_window);
}

int main(void) {
  init();
  app_event_loop();
  deinit();
}