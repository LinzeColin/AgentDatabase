// macOS 自带 Vision OCR，走 Objective-C（不碰 swiftinterface）。
// ★ 只识别，不清洗——照录，讹字保留。
#import <Foundation/Foundation.h>
#import <Vision/Vision.h>
#import <ImageIO/ImageIO.h>
#import <CoreGraphics/CoreGraphics.h>

int main(int argc, const char *argv[]) {
  @autoreleasepool {
    if (argc < 2) { fprintf(stderr, "用法: ocr <图片…>\n"); return 3; }
    int failed = 0;
    for (int i = 1; i < argc; i++) {
      NSString *path = [NSString stringWithUTF8String:argv[i]];
      NSURL *url = [NSURL fileURLWithPath:path];
      CGImageSourceRef src = CGImageSourceCreateWithURL((__bridge CFURLRef)url, NULL);
      if (!src) { fprintf(stderr, "✗ 打不开 %s\n", argv[i]); failed++; continue; }
      CGImageRef cg = CGImageSourceCreateImageAtIndex(src, 0, NULL);
      CFRelease(src);
      if (!cg) { fprintf(stderr, "✗ 解码失败 %s\n", argv[i]); failed++; continue; }

      VNRecognizeTextRequest *req = [[VNRecognizeTextRequest alloc] init];
      req.recognitionLevel = VNRequestTextRecognitionLevelAccurate;
      req.usesLanguageCorrection = NO;      // ★ 要照录，不要它替我猜
      VNImageRequestHandler *h = [[VNImageRequestHandler alloc] initWithCGImage:cg options:@{}];
      NSError *err = nil;
      [h performRequests:@[req] error:&err];
      if (err) { fprintf(stderr, "✗ 识别失败 %s: %s\n", argv[i], err.localizedDescription.UTF8String); failed++; CGImageRelease(cg); continue; }
      NSArray *obs = req.results;
      printf("=== %s === %zux%zu %lu 行\n", path.lastPathComponent.UTF8String,
             CGImageGetWidth(cg), CGImageGetHeight(cg), (unsigned long)obs.count);
      for (VNRecognizedTextObservation *o in obs) {
        NSArray *c = [o topCandidates:1];
        if (c.count) printf("%s\n", [(VNRecognizedText *)c[0] string].UTF8String);
      }
      CGImageRelease(cg);
    }
    return failed ? 1 : 0;
  }
}
