import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

public class AddWaterMarkOnImage {

    public static void addTextWaterMark(BufferedImage targetImg, Color textColor, int fontSize, String text, String outPath) {
        try {

            int width = targetImg.getWidth(); //图片宽
            int height = targetImg.getHeight(); //图片高


            BufferedImage bufferedImage = new BufferedImage(width, height, BufferedImage.TYPE_INT_BGR);
            Graphics2D g = bufferedImage.createGraphics();
            g.drawImage(targetImg, 0, 0, width, height, null);

            g.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_ATOP, 0.3f));
            g.rotate(-Math.toRadians(45));//设置水印逆时针旋转20度
            g.setFont(new Font("微软雅黑", Font.ITALIC, fontSize));
            g.setColor(textColor); //水印颜色


            for (float w = -width; w < width; w += width / 8f) {
                for (float h =0; h <  2.5*height; h += height / 25f) {
                    // 水印内容放置在右下角
                    g.drawString(text, w, h);
                }
            }

            g.dispose();
            FileOutputStream outImgStream = new FileOutputStream(outPath);
            ImageIO.write(bufferedImage, "jpg", outImgStream);
            outImgStream.flush();
            outImgStream.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) throws IOException {
        File file = new File("/path/to/image");
        BufferedImage image = ImageIO.read(file);
        AddWaterMarkOnImage.addTextWaterMark(image, Color.GRAY, 20, "water mark contents", "/path/to/output/image");
    }

}
