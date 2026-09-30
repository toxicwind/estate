package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000*\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\u0019\u0012\u0010\b\u0002\u0010\u0002\u001a\n\u0012\u0004\u0012\u00020\u0004\u0018\u00010\u0003¢\u0006\u0004\b\u0005\u0010\u0006J\u0011\u0010\t\u001a\n\u0012\u0004\u0012\u00020\u0004\u0018\u00010\u0003HÆ\u0003J\u001b\u0010\n\u001a\u00020\u00002\u0010\b\u0002\u0010\u0002\u001a\n\u0012\u0004\u0012\u00020\u0004\u0018\u00010\u0003HÆ\u0001J\u0014\u0010\u000b\u001a\u00020\f2\b\u0010\r\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u000e\u001a\u00020\u000fHÖ\u0081\u0004J\n\u0010\u0010\u001a\u00020\u0011HÖ\u0081\u0004R\u0019\u0010\u0002\u001a\n\u0012\u0004\u0012\u00020\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0007\u0010\b¨\u0006\u0012"}, d2 = {"LXhamster/VideoListProps;", "", "videoThumbProps", "", "LXhamster/VideoThumbProps;", "<init>", "(Ljava/util/List;)V", "getVideoThumbProps", "()Ljava/util/List;", "component1", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class VideoListProps {

    @org.jetbrains.annotations.Nullable
    private final java.util.List<Xhamster.VideoThumbProps> videoThumbProps;

    /* JADX WARN: Illegal instructions before constructor call */
    public VideoListProps() {
        java.util.List list = null;
        this(list, 1, list);
    }

    /* JADX WARN: Multi-variable type inference failed */
    public static /* synthetic */ Xhamster.VideoListProps copy$default(Xhamster.VideoListProps videoListProps, java.util.List list, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            list = videoListProps.videoThumbProps;
        }
        return videoListProps.copy(list);
    }

    @org.jetbrains.annotations.Nullable
    public final java.util.List<Xhamster.VideoThumbProps> component1() {
        return this.videoThumbProps;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.VideoListProps copy(@org.jetbrains.annotations.Nullable java.util.List<Xhamster.VideoThumbProps> videoThumbProps) {
        return new Xhamster.VideoListProps(videoThumbProps);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        return (other instanceof Xhamster.VideoListProps) && kotlin.jvm.internal.Intrinsics.areEqual(this.videoThumbProps, ((Xhamster.VideoListProps) other).videoThumbProps);
    }

    public int hashCode() {
        if (this.videoThumbProps == null) {
            return 0;
        }
        return this.videoThumbProps.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "VideoListProps(videoThumbProps=" + this.videoThumbProps + ')';
    }

    public VideoListProps(@org.jetbrains.annotations.Nullable java.util.List<Xhamster.VideoThumbProps> list) {
        this.videoThumbProps = list;
    }

    public /* synthetic */ VideoListProps(java.util.List list, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : list);
    }

    @org.jetbrains.annotations.Nullable
    public final java.util.List<Xhamster.VideoThumbProps> getVideoThumbProps() {
        return this.videoThumbProps;
    }
}
